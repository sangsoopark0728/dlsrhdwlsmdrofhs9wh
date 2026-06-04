#!/usr/bin/env python3
"""
📚 Study Timer App — 공부 타이머 (커스텀 버전)  
부드러운 60fps 애니메이션 버전
"""

import os
import sys

_BUILT_FLAG = os.environ.get("STUDY_TIMER_APP")
_IS_FROZEN  = getattr(sys, "frozen", False)

if False:
    import subprocess
    import shutil
    import platform

    script_path = os.path.abspath(__file__)
    script_dir  = os.path.dirname(script_path)
    dist_dir    = os.path.join(script_dir, "dist")

    if platform.system() == "Windows":
        out_name = "StudyTimer.exe"
    else:
        out_name = "StudyTimer"
    out_path = os.path.join(dist_dir, out_name)

    if os.path.exists(out_path):
        print(f"[StudyTimer] 실행파일 발견: {out_path}")
        print("[StudyTimer] 앱을 실행합니다...")
        os.execv(out_path, [out_path])
        sys.exit(0)

    print("=" * 55)
    print("  📚 Study Timer — 첫 실행 빌드")
    print("  실행파일을 생성합니다. 잠시만 기다려주세요...")
    print("=" * 55)

    try:
        import PyInstaller
    except ImportError:
        print("\n[1/2] PyInstaller 설치 중...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller", "-q"],
            stdout=subprocess.DEVNULL,
        )
        print("      PyInstaller 설치 완료 ✓")

    print("\n[2/2] 실행파일 빌드 중...")
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "StudyTimer",
        "--distpath", dist_dir,
        "--workpath", os.path.join(script_dir, "build"),
        "--specpath", script_dir,
        "--noconfirm",
        script_path,
    ] # <- 오타가 났던 괄호 위치를 정상적으로 수정했습니다.
    
    result = subprocess.run(build_cmd, capture_output=True, text=True)

    if result.returncode != 0 or not os.path.exists(out_path):
        import sys
        print("\n[오류] 빌드 실패. 오류 내용:")
        print(result.stderr[-2000:])
        sys.exit(1)

    spec_file = os.path.join(script_dir, "StudyTimer.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
    build_path = os.path.join(script_dir, "build")
    if os.path.exists(build_path):
        shutil.rmtree(build_path, ignore_errors=True)

    print(f"\n✅ 빌드 완료!\n→ {out_path}\n   앱을 실행합니다...\n")

    if platform.system() == "Windows":
        subprocess.Popen([out_path])
        sys.exit(0)
    else:
        os.chmod(out_path, 0o755)
        os.execv(out_path, [out_path])
    sys.exit(0)

# ══════════════════════════════════════════════════════════
#  실제 앱 코드
# ══════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import messagebox
import math
import time

# 팔레트
BG         = "#0f1117"
SIDEBAR_BG = "#161b22"
CARD_BG    = "#1c2333"
BORDER     = "#30363d"
TEXT       = "#e6edf3"
TEXT_DIM   = "#8b949e"
ACCENT     = "#58a6ff"
SUCCESS    = "#3fb950"
WARNING    = "#d29922"
DANGER     = "#f85149"

SUBJECT_COLORS = [
    "#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#ffa657",
    "#79c0ff", "#56d364", "#ff7b72", "#e3b341", "#bc8cff",
]

FRAME_MS = 16

class StudyTimerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📚 Study Timer")
        self.geometry("1100x700")
        self.minsize(950, 650)
        self.configure(bg=BG)
        self.resizable(True, True)

        # 상태
        self.subjects     = []
        self.character    = tk.StringVar(value="turtle")
        self.prop         = tk.StringVar(value="box")

        # 타이머 상태
        self.timer_running   = False
        self.timer_paused    = False
        self.current_subject = 0
        self.total_secs      = 0
        self._start_mono     = 0.0
        self._elapsed_at_pause = 0.0
        self._anim_id        = None

        # 애니메이션 내부 상태
        self.anim_w        = 800
        self.anim_h        = 140
        self.anim_ground   = 120
        self.anim_color    = ACCENT
        self.anim_start_x  = 40
        self.anim_end_x    = 760
        self.anim_progress = 0.0

        self._build_ui()

    def _build_ui(self):
        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        logo_frame.pack(fill="x", pady=(24, 8), padx=16)
        tk.Label(logo_frame, text="📚", font=("Segoe UI Emoji", 28), bg=SIDEBAR_BG, fg=TEXT).pack()
        tk.Label(logo_frame, text="Study Timer", font=("Georgia", 14, "bold"), bg=SIDEBAR_BG, fg=TEXT).pack()
        tk.Label(logo_frame, text="공부 타이머", font=("Malgun Gothic", 9), bg=SIDEBAR_BG, fg=TEXT_DIM).pack()

        self._divider(self.sidebar)

        # 캐릭터 선택
        self._section_label(self.sidebar, "🐾 캐릭터 선택")
        char_list = [
            ("turtle", "거북이", "🐢"), 
            ("rabbit", "토끼", "🐰"),
            ("dino", "공룡", "🦖"),
            ("cat", "고양이", "🐱"),
            ("dog", "강아지", "🐶")
        ]
        for val, label, icon in char_list:
            self._radio_btn(self.sidebar, label, icon, val, self.character)

        self._divider(self.sidebar)

        self._section_label(self.sidebar, "📦 소품 선택")
        for val, label, icon in [("box", "박스", "📦"), ("ball", "공", "⚽")]:
            self._radio_btn(self.sidebar, label, icon, val, self.prop)

        self._divider(self.sidebar)

        self._section_label(self.sidebar, "➕ 과목 추가")
        add_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG, padx=12)
        add_frame.pack(fill="x", pady=4)

        tk.Label(add_frame, text="과목명", font=("Malgun Gothic", 9), bg=SIDEBAR_BG, fg=TEXT_DIM).pack(anchor="w")
        self.entry_subject = self._entry(add_frame)
        self.entry_subject.pack(fill="x", pady=(2, 6))

        tk.Label(add_frame, text="공부 시간 (분)", font=("Malgun Gothic", 9), bg=SIDEBAR_BG, fg=TEXT_DIM).pack(anchor="w")
        self.entry_minutes = self._entry(add_frame)
        self.entry_minutes.pack(fill="x", pady=(2, 8))

        tk.Button(add_frame, text="+ 과목 추가", font=("Malgun Gothic", 10, "bold"),
                  bg=ACCENT, fg="#000000", activebackground="#79c0ff",
                  relief="flat", cursor="hand2", pady=6,
                  command=self._add_subject).pack(fill="x")

        bottom = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        bottom.pack(side="bottom", fill="x", padx=12, pady=16)
        tk.Button(bottom, text="↺  초기화", font=("Malgun Gothic", 9),
                  bg=CARD_BG, fg=TEXT_DIM, activebackground=BORDER,
                  relief="flat", cursor="hand2", pady=4,
                  command=self._reset_all).pack(fill="x")

    def _build_main(self):
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self._build_schedule_view()
        self._build_timer_view()
        self.schedule_view.pack(fill="both", expand=True)

    def _build_schedule_view(self):
        self.schedule_view = tk.Frame(self.main, bg=BG)

        content_frame = tk.Frame(self.schedule_view, bg=BG)
        content_frame.pack(fill="both", expand=True, padx=32, pady=32)

        hdr = tk.Frame(content_frame, bg=BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="오늘의 공부 시간표", font=("Georgia", 22, "bold"), bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text="왼쪽 메뉴에서 과목을 추가하고 타이머를 시작하세요.",
                 font=("Malgun Gothic", 11), bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        list_frame = tk.Frame(content_frame, bg=BG)
        list_frame.pack(fill="both", expand=True, pady=20)

        canvas = tk.Canvas(list_frame, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.subject_list_frame = tk.Frame(canvas, bg=BG)
        self.subject_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.subject_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.empty_label = tk.Label(self.subject_list_frame,
                                    text="아직 과목이 없습니다.\n왼쪽 메뉴에서 과목을 추가해주세요! ✏️",
                                    font=("Malgun Gothic", 13), bg=BG, fg=TEXT_DIM, justify="center")
        self.empty_label.pack(pady=60)

        # 오른쪽 하단 타이머 대형 시작 버튼
        btn_frame = tk.Frame(content_frame, bg=BG)
        btn_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        self.start_btn = tk.Button(btn_frame, text="▶  공부 타이머 시작하기",
                                   font=("Malgun Gothic", 14, "bold"),
                                   bg="#ff7b72", fg="#000000", activebackground="#f78166",
                                   relief="flat", cursor="hand2", padx=30, pady=15)
        self.start_btn.configure(command=self._start_timer)
        self.start_btn.pack(side="right")

    def _build_timer_view(self):
        self.timer_view = tk.Frame(self.main, bg=BG)

        top = tk.Frame(self.timer_view, bg=BG)
        top.pack(fill="x", padx=40, pady=(36, 0))
        self.lbl_subject_name = tk.Label(top, text="", font=("Georgia", 20, "bold"), bg=BG, fg=ACCENT)
        self.lbl_subject_name.pack()
        self.lbl_subject_index = tk.Label(top, text="", font=("Malgun Gothic", 11), bg=BG, fg=TEXT_DIM)
        self.lbl_subject_index.pack(pady=(2, 0))

        self.lbl_timer = tk.Label(self.timer_view, text="00:00", font=("Courier New", 72, "bold"), bg=BG, fg=TEXT)
        self.lbl_timer.pack(pady=(8, 0))

        pb_frame = tk.Frame(self.timer_view, bg=BG, padx=40)
        pb_frame.pack(fill="x", pady=(4, 0))
        self.progress_canvas = tk.Canvas(pb_frame, height=8, bg=CARD_BG, highlightthickness=0, bd=0)
        self.progress_canvas.pack(fill="x")
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 8, fill=ACCENT, outline="")

        anim_frame = tk.Frame(self.timer_view, bg=BG, padx=40)
        anim_frame.pack(fill="x", pady=(18, 0))
        self.anim_canvas = tk.Canvas(anim_frame, height=140, bg=CARD_BG, highlightthickness=1, bd=0, highlightbackground=BORDER)
        self.anim_canvas.pack(fill="x")
        self.anim_canvas.bind("<Configure>", self._on_canvas_resize)

        ctrl = tk.Frame(self.timer_view, bg=BG)
        ctrl.pack(pady=20)
        self.pause_btn = tk.Button(ctrl, text="⏸  일시정지", font=("Malgun Gothic", 13, "bold"),
                                   bg=WARNING, fg="#000000", activebackground="#e3b341",
                                   relief="flat", cursor="hand2", padx=24, pady=10, command=self._toggle_pause)
        self.pause_btn.pack(side="left", padx=8)
        
        tk.Button(ctrl, text="⏭  다음 과목", font=("Malgun Gothic", 13),
                  bg=CARD_BG, fg=TEXT, activebackground=BORDER,
                  relief="flat", cursor="hand2", padx=24, pady=10, command=self._next_subject).pack(side="left", padx=8)

        self.mini_schedule = tk.Frame(self.timer_view, bg=BG)
        self.mini_schedule.pack(fill="x", padx=40, pady=(10, 0))

    def _add_subject(self):
        name = self.entry_subject.get().strip()
        mins = self.entry_minutes.get().strip()
        if not name:
            messagebox.showwarning("입력 오류", "과목명을 입력해주세요.")
            return
        try:
            mins = int(mins)
            if mins <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("입력 오류", "공부 시간을 올바른 양수로 입력해주세요.")
            return
        color = SUBJECT_COLORS[len(self.subjects) % len(SUBJECT_COLORS)]
        self.subjects.append({"name": name, "minutes": mins, "color": color})
        self.entry_subject.delete(0, "end")
        self.entry_minutes.delete(0, "end")
        self._refresh_subject_list()

    def _remove_subject(self, idx):
        if self.timer_running:
            messagebox.showinfo("안내", "타이머 실행 중에는 과목을 삭제할 수 없습니다.")
            return
        self.subjects.pop(idx)
        for i, s in enumerate(self.subjects):
            s["color"] = SUBJECT_COLORS[i % len(SUBJECT_COLORS)]
        self._refresh_subject_list()

    def _refresh_subject_list(self):
        for w in self.subject_list_frame.winfo_children():
            w.destroy()
        if not self.subjects:
            tk.Label(self.subject_list_frame, text="아직 과목이 없습니다.\n왼쪽 메뉴에서 과목을 추가해주세요! ✏️",
                     font=("Malgun Gothic", 13), bg=BG, fg=TEXT_DIM, justify="center").pack(pady=60)
            return
        for i, subj in enumerate(self.subjects):
            card = tk.Frame(self.subject_list_frame, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", pady=5)
            tk.Frame(card, bg=subj["color"], width=6).pack(side="left", fill="y")
            body = tk.Frame(card, bg=CARD_BG, padx=16, pady=12)
            body.pack(side="left", fill="both", expand=True)
            row1 = tk.Frame(body, bg=CARD_BG)
            row1.pack(fill="x")
            tk.Label(row1, text=f"{i+1:02d}.", font=("Courier New", 14, "bold"), bg=CARD_BG, fg=subj["color"], width=3, anchor="w").pack(side="left")
            tk.Label(row1, text=subj["name"], font=("Malgun Gothic", 14, "bold"), bg=CARD_BG, fg=TEXT).pack(side="left", padx=6)
            tk.Button(row1, text="✕", font=("Malgun Gothic", 10), bg=CARD_BG, fg=DANGER, activebackground=CARD_BG,
                      relief="flat", cursor="hand2", bd=0, command=lambda i=i: self._remove_subject(i)).pack(side="right", padx=4)
            tk.Label(body, text=f"⏱  {subj['minutes']}분", font=("Malgun Gothic", 11), bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

    def _start_timer(self):
        if not self.subjects:
            messagebox.showwarning("과목 없음", "먼저 과목을 추가해주세요.")
            return
        self.timer_running   = True
        self.timer_paused    = False
        self.current_subject = 0
        self.schedule_view.pack_forget()
        self.timer_view.pack(fill="both", expand=True)
        self._load_subject(0)

    def _load_subject(self, idx):
        if idx >= len(self.subjects):
            self._all_done()
            return
        self.current_subject      = idx
        subj                      = self.subjects[idx]
        self.total_secs           = subj["minutes"] * 60
        self._elapsed_at_pause    = 0.0
        self._start_mono          = time.monotonic()
        color = subj["color"]

        self.lbl_subject_name.configure(text=subj["name"], fg=color)
        self.lbl_subject_index.configure(text=f"과목 {idx+1} / {len(self.subjects)}")
        self.lbl_timer.configure(fg=color)
        self.progress_canvas.itemconfigure(self.progress_bar, fill=color)
        self._refresh_mini_schedule(idx, color)

        self.anim_progress = 0.0
        self.anim_color    = color
        self._rebuild_track()

        self._stop_loops()
        self._render_loop()

    def _stop_loops(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None

    def _elapsed(self):
        if self.timer_paused:
            return self._elapsed_at_pause
        return self._elapsed_at_pause + (time.monotonic() - self._start_mono)

    def _render_loop(self):
        if not self.timer_running:
            return

        elapsed  = self._elapsed()
        remaining = max(0.0, self.total_secs - elapsed)
        progress  = elapsed / self.total_secs if self.total_secs > 0 else 0.0
        progress  = min(progress, 1.0)

        remaining_ceil = math.ceil(remaining)
        mins, secs = divmod(remaining_ceil, 60)
        self.lbl_timer.configure(text=f"{mins:02d}:{secs:02d}")

        w = self.progress_canvas.winfo_width()
        if w > 0:
            self.progress_canvas.coords(self.progress_bar, 0, 0, w * progress, 8)

        if not self.timer_paused:
            diff = progress - self.anim_progress
            self.anim_progress += diff * 0.06
        self._draw_scene(self.anim_progress)

        if elapsed >= self.total_secs:
            self._subject_done()
            return

        self._anim_id = self.after(FRAME_MS, self._render_loop)

    def _toggle_pause(self):
        if not self.timer_running:
            return
        if not self.timer_paused:
            self._elapsed_at_pause = self._elapsed()
            self.timer_paused = True
            self.pause_btn.configure(text="▶  재개", bg=SUCCESS)
        else:
            self._start_mono  = time.monotonic()
            self.timer_paused = False
            self.pause_btn.configure(text="⏸  일시정지", bg=WARNING)
            self._render_loop()

    def _next_subject(self):
        self._stop_loops()
        self._load_subject(self.current_subject + 1)

    def _subject_done(self):
        self._stop_loops()
        self.lbl_timer.configure(text="완료! ✓")
        self.anim_progress = 1.0
        self._draw_scene(1.0)
        self.after(1200, lambda: self._load_subject(self.current_subject + 1))

    def _all_done(self):
        self._stop_loops()
        self.timer_running = False
        self.lbl_subject_name.configure(text="🎉 모든 공부 완료!", fg=SUCCESS)
        self.lbl_subject_index.configure(text="수고했어요!")
        self.lbl_timer.configure(text="00:00", fg=SUCCESS)
        self.pause_btn.configure(state="disabled")
        self._draw_scene(1.0)
        messagebox.showinfo("완료!", "오늘의 공부를 모두 마쳤습니다! 🎉\n수고했어요!")

    def _reset_all(self):
        self._stop_loops()
        self.timer_running        = False
        self.timer_paused         = False
        self.anim_progress        = 0.0
        self._elapsed_at_pause    = 0.0
        self.timer_view.pack_forget()
        self.schedule_view.pack(fill="both", expand=True)
        self.pause_btn.configure(text="⏸  일시정지", bg=WARNING, state="normal")

    def _refresh_mini_schedule(self, current_idx, color):
        for w in self.mini_schedule.winfo_children():
            w.destroy()
        tk.Label(self.mini_schedule, text="시간표", font=("Malgun Gothic", 10), bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(0, 6))
        row = tk.Frame(self.mini_schedule, bg=BG)
        row.pack(fill="x")
        for i, subj in enumerate(self.subjects):
            if i < current_idx:
                sc, st, ab = TEXT_DIM, "✓", CARD_BG
            elif i == current_idx:
                sc, st, ab = subj["color"], "▶", CARD_BG
            else:
                sc, st, ab = BORDER, "○", BG
            pill = tk.Frame(row, bg=ab, highlightthickness=1, highlightbackground=sc if i == current_idx else BORDER)
            pill.pack(side="left", padx=4, pady=2)
            tk.Label(pill, text=f"{st} {subj['name']} ({subj['minutes']}분)",
                     font=("Malgun Gothic", 9), bg=ab, fg=sc, padx=8, pady=4).pack()

    def _on_canvas_resize(self, event):
        self._rebuild_track()
        self._draw_scene(self.anim_progress)

    def _rebuild_track(self):
        c  = self.anim_canvas
        w  = c.winfo_width()  or 800
        h  = c.winfo_height() or 140
        gy = h - 22

        self.anim_w       = w
        self.anim_h       = h
        self.anim_ground  = gy
        self.anim_start_x = 50
        self.anim_end_x   = w - 50

        c.delete("all")
        color = self.anim_color

        for i in range(0, h - 30, 4):
            t = i / (h - 30)
            r = int(0x1c + t * (0x0f - 0x1c))
            g = int(0x23 + t * (0x11 - 0x23))
            b = int(0x33 + t * (0x17 - 0x33))
            shade = f"#{r:02x}{g:02x}{b:02x}"
            c.create_line(0, i, w, i, fill=shade, tags="bg")

        c.create_rectangle(0, gy, w, h, fill="#1a2e1a", outline="", tags="bg")
        c.create_rectangle(0, gy, w, gy + 4, fill="#2d5a1b", outline="", tags="bg")

        for x in range(self.anim_start_x + 20, self.anim_end_x - 20, 28):
            c.create_line(x, gy - 1, x + 14, gy - 1, fill="#2d3f2d", width=2, tags="bg")

        sx = self.anim_start_x
        c.create_rectangle(sx - 18, gy - 32, sx + 18, gy - 10, fill="#2d3748", outline=TEXT_DIM, width=1, tags="bg")
        c.create_text(sx, gy - 21, text="START", fill=TEXT_DIM, font=("Courier New", 7, "bold"), tags="bg")

        ex = self.anim_end_x
        c.create_line(ex, gy - 50, ex, gy, fill=color, width=2, tags="bg")
        c.create_polygon(ex, gy - 50, ex + 22, gy - 41, ex, gy - 32, fill=color, outline="", tags="bg")
        c.create_text(ex, gy + 10, text="END", fill=color, font=("Courier New", 7, "bold"), tags="bg")

        for cx_c, cy_c, r_c in [(w * 0.25, 18, 14), (w * 0.6, 12, 10), (w * 0.8, 20, 12)]:
            c.create_oval(cx_c - r_c, cy_c - r_c * 0.6, cx_c + r_c, cy_c + r_c * 0.6, fill="#2a3a4a", outline="", tags="bg")
            c.create_oval(cx_c - r_c * 0.5, cy_c - r_c, cx_c + r_c * 0.5, cy_c + r_c * 0.2, fill="#2a3a4a", outline="", tags="bg")

    def _draw_scene(self, progress):
        c   = self.anim_canvas
        gy  = self.anim_ground
        t   = time.time()

        travel = self.anim_end_x - self.anim_start_x
        char_x = self.anim_start_x + travel * progress

        c.delete("dyn")

        char  = self.character.get()
        prop_ = self.prop.get()
        color = self.anim_color

        c.create_oval(char_x - 20, gy - 4, char_x + 20, gy + 4, fill="#0a1010", outline="", tags="dyn")

        prop_offset = 32
        px = char_x + prop_offset
        if px > self.anim_end_x + 8:
            px = self.anim_end_x + 8

        if prop_ == "box":
            self._draw_box(c, px, gy, progress, t, color)
        else:
            self._draw_ball(c, px, gy, progress, t, color)

        if char == "turtle":
            self._draw_turtle(c, char_x, gy, t, color)
        elif char == "rabbit":
            self._draw_rabbit(c, char_x, gy, t, color)
        elif char == "dino":
            self._draw_dino(c, char_x, gy, t, color)
        elif char == "cat":
            self._draw_cat(c, char_x, gy, t, color)
        elif char == "dog":
            self._draw_dog(c, char_x, gy, t, color)

    def _draw_box(self, c, px, gy, progress, t, color):
        if self.timer_paused:
            wobble, tilt = 0.0, 0
        else:
            wobble = math.sin(t * 12) * 1.5
            tilt   = int(math.sin(t * 8) * 2)

        bx, by = px, gy - 28 + wobble
        c.create_polygon(bx + 14, by, bx + 20, by - 6, bx + 20, by + 22 - 6, bx + 14, by + 22, fill=self._darken(color, 0.55), outline="", tags="dyn")
        c.create_polygon(bx - 14, by, bx + 14, by, bx + 20, by - 6, bx - 8,  by - 6, fill=self._lighten(color, 0.3), outline="", tags="dyn")
        c.create_rectangle(bx - 14 + tilt, by, bx + 14 + tilt, by + 22, fill=color, outline=self._darken(color, 0.4), width=1, tags="dyn")
        
        mid_y = by + 11
        c.create_line(bx - 14 + tilt, mid_y, bx + 14 + tilt, mid_y, fill=self._darken(color, 0.35), width=1, tags="dyn")
        c.create_line(bx + tilt, by, bx + tilt, by + 22, fill=self._darken(color, 0.35), width=1, tags="dyn")
        c.create_oval(bx - 10, gy - 3, bx + 18, gy + 3, fill="#0a1010", outline="", tags="dyn")

    def _draw_ball(self, c, px, gy, progress, t, color):
        r = 14
        if self.timer_paused:
            bounce, angle = 0.0, 0.0
        else:
            bounce = abs(math.sin(t * 8)) * 5
            angle  = t * 5.0

        cy_ball = gy - r - bounce
        c.create_oval(px - r * 0.9, gy - 4, px + r * 0.9, gy + 3, fill="#0a1010", outline="", tags="dyn")
        c.create_oval(px - r, cy_ball - r, px + r, cy_ball + r, fill=color, outline=self._darken(color, 0.35), width=2, tags="dyn")
        c.create_oval(px - r * 0.5, cy_ball - r * 0.7, px - r * 0.05, cy_ball - r * 0.25, fill=self._lighten(color, 0.45), outline="", tags="dyn")

        for offset_angle in [0, math.pi]:
            a = angle + offset_angle
            cx_line = px + math.sin(a) * r * 0.7
            c.create_arc(cx_line - r * 0.3, cy_ball - r, cx_line + r * 0.3, cy_ball + r,
                          start=0, extent=180 if math.cos(a) >= 0 else -180,
                          style="arc", outline=self._darken(color, 0.3), width=1, tags="dyn")

    def _draw_turtle(self, c, cx, gy, t, color):
        if self.timer_paused:
            walk, bob = 0.0, 0.0
        else:
            walk, bob = t * 3.5, math.sin(t * 7) * 1.8
        cy = gy - 24 + bob

        c.create_oval(cx - 26, cy - 3, cx - 14, cy + 7, fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")
        for lx, phase in [(-14, 0), (-6, math.pi)]:
            swing = math.sin(walk + phase) * 6
            lby   = cy + 12 + swing
            c.create_oval(cx + lx - 7, lby - 5, cx + lx + 7, lby + 5, fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")
            c.create_oval(cx + lx - 5, lby + 1, cx + lx + 5, lby + 8, fill="#2e6b4f", outline="#1b4332", width=1, tags="dyn")

        c.create_oval(cx - 22, cy - 16, cx + 22, cy + 14, fill="#2d6a4f", outline="#1b4332", width=2, tags="dyn")
        c.create_oval(cx - 18, cy - 20, cx + 18, cy + 6, fill=color, outline=self._darken(color, 0.4), width=2, tags="dyn")
        
        sc = self._darken(color, 0.25)
        c.create_oval(cx - 8, cy - 17, cx + 8, cy - 4, fill=self._darken(color, 0.15), outline=sc, width=1, tags="dyn")
        c.create_oval(cx - 14, cy - 9, cx - 3, cy + 2, fill=self._darken(color, 0.15), outline=sc, width=1, tags="dyn")
        c.create_oval(cx + 3, cy - 9, cx + 14, cy + 2, fill=self._darken(color, 0.15), outline=sc, width=1, tags="dyn")

        for lx, phase in [(8, math.pi), (16, 0)]:
            swing = math.sin(walk + phase) * 6
            lby   = cy + 10 + swing
            c.create_oval(cx + lx - 6, lby - 5, cx + lx + 6, lby + 5, fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")
            c.create_oval(cx + lx - 5, lby + 1, cx + lx + 5, lby + 8, fill="#2e6b4f", outline="#1b4332", width=1, tags="dyn")

        c.create_oval(cx + 16, cy - 8, cx + 28, cy + 4, fill="#40916c", outline="#1b4332", width=1, tags="dyn")
        hx, hy = cx + 30, cy - 12
        c.create_oval(hx - 13, hy - 10, hx + 13, hy + 14, fill="#40916c", outline="#1b4332", width=2, tags="dyn")

        ex, ey = hx + 3, hy - 2
        c.create_oval(ex - 5, ey - 5, ex + 5, ey + 5, fill="white", outline="#1b4332", width=1, tags="dyn")
        c.create_oval(ex - 2, ey - 2, ex + 3, ey + 3, fill="#1a1a2e", tags="dyn")
        c.create_oval(ex - 1, ey - 4, ex + 1, ey - 2, fill="white", tags="dyn")
        c.create_arc(hx - 5, hy + 2, hx + 7, hy + 12, start=200, extent=-160, style="arc", outline="#1b4332", width=2, tags="dyn")
        c.create_oval(hx + 5, hy + 2, hx + 9, hy + 5, fill="#2e6b4f", outline="", tags="dyn")

    def _draw_rabbit(self, c, cx, gy, t, color):
        if self.timer_paused:
            walk, bob, ear_sway = 0.0, 0.0, 0.0
        else:
            walk, bob, ear_sway = t * 5.0, math.sin(t * 10) * 2.5, math.sin(t * 4) * 3
        cy = gy - 28 + bob

        c.create_oval(cx - 26, cy + 2, cx - 12, cy + 16, fill="white", outline="#d0c8cc", width=1, tags="dyn")
        c.create_oval(cx - 24, cy + 4, cx - 15, cy + 14, fill="#f0eaec", outline="", tags="dyn")

        for lx, phase in [(-12, 0), (0, math.pi)]:
            swing = math.sin(walk + phase) * 7
            lby   = cy + 14 + swing
            c.create_oval(cx + lx - 10, lby - 4, cx + lx + 10, lby + 6, fill="#f0e6eb", outline="#c9b2c5", width=1, tags="dyn")
            for toe in [-4, 0, 4]:
                c.create_oval(cx + lx + toe - 2, lby + 3, cx + lx + toe + 2, lby + 7, fill="#e8d8e0", outline="", tags="dyn")

        c.create_oval(cx - 20, cy - 14, cx + 20, cy + 18, fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        c.create_oval(cx - 10, cy - 4, cx + 12, cy + 14, fill="#faf4f7", outline="", tags="dyn")

        for lx, phase in [(10, math.pi), (18, 0)]:
            swing = math.sin(walk + phase) * 5
            lby   = cy + 10 + swing
            c.create_oval(cx + lx - 7, lby - 4, cx + lx + 7, lby + 5, fill="#f0e6eb", outline="#c9b2c5", width=1, tags="dyn")

        hx, hy = cx + 20, cy - 20
        c.create_oval(hx - 15, hy - 12, hx + 15, hy + 15, fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        c.create_oval(hx + 5, hy + 3, hx + 13, hy + 11, fill="#f4c2cc", outline="", tags="dyn")

        ear_dx = ear_sway * 0.5
        c.create_oval(hx - 2 + ear_dx, hy - 42, hx + 8 + ear_dx, hy - 12, fill="#f0e8ed", outline="#c9b2c5", width=1, tags="dyn")
        c.create_oval(hx, hy - 40 + ear_dx * 0.3, hx + 6, hy - 14, fill=self._lighten(color, 0.2), outline="", tags="dyn")

        c.create_oval(hx - 12 - ear_dx, hy - 44, hx - 2 - ear_dx, hy - 12, fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        c.create_oval(hx - 10 - ear_dx, hy - 42, hx - 4 - ear_dx, hy - 14, fill=self._lighten(color, 0.2), outline="", tags="dyn")

        ex, ey = hx + 6, hy - 4
        c.create_oval(ex - 5, ey - 5, ex + 5, ey + 5, fill="white", outline="#c9b2c5", width=1, tags="dyn")
        c.create_oval(ex - 2, ey - 2, ex + 3, ey + 3, fill="#2a1a2e", tags="dyn")
        c.create_oval(ex - 1, ey - 4, ex + 1, ey - 2, fill="white", tags="dyn")
        c.create_oval(hx + 8, hy + 3, hx + 14, hy + 8, fill="#f9a8c9", outline="", tags="dyn")

        for wy, wlen in [(hy + 2, 12), (hy + 5, 10), (hy + 8, 11)]:
            c.create_line(hx + 8, wy, hx + 8 + wlen, wy - 1, fill="#d0bcc5", width=1, tags="dyn")

        c.create_arc(hx + 5, hy + 6, hx + 14, hy + 14, start=220, extent=-140, style="arc", outline="#c9b2c5", width=1, tags="dyn")

    def _draw_dino(self, c, cx, gy, t, color):
        if self.timer_paused:
            walk, bob, tail_wobble = 0.0, 0.0, 0.0
        else:
            walk, bob, tail_wobble = t * 4.5, math.sin(t * 9) * 2.0, math.sin(t * 6) * 4
        cy = gy - 26 + bob

        c.create_polygon(cx - 18, cy + 5, cx - 38, cy + 12 + tail_wobble, cx - 14, cy + 16, fill="#2a7a43", outline="#133a1e", tags="dyn")
        for spike_x, spike_y in [(cx-12, cy-14), (cx-4, cy-17), (cx+4, cy-14)]:
            c.create_polygon(spike_x, spike_y, spike_x - 4, spike_y - 6, spike_x - 8, spike_y, fill=color, outline="", tags="dyn")

        for lx, phase in [(-8, 0), (4, math.pi)]:
            swing = math.sin(walk + phase) * 6
            lby   = cy + 14 + swing
            c.create_rectangle(cx + lx - 4, cy + 8, cx + lx + 4, lby + 6, fill="#2a7a43", outline="#133a1e", tags="dyn")
            c.create_oval(cx + lx - 5, lby + 3, cx + lx + 6, lby + 8, fill="#1f5c31", outline="", tags="dyn")

        c.create_oval(cx - 18, cy - 12, cx + 14, cy + 16, fill="#2a7a43", outline="#133a1e", width=2, tags="dyn")
        c.create_polygon(cx + 4, cy, cx + 22, cy - 24, cx + 36, cy - 20, cx + 14, cy + 12, fill="#2a7a43", outline="#133a1e", tags="dyn")
        c.create_oval(cx + 14, cy - 30, cx + 38, cy - 10, fill="#2a7a43", outline="#133a1e", width=2, tags="dyn")

        c.create_oval(cx + 26, cy - 26, cx + 34, cy - 18, fill="white", outline="#133a1e", tags="dyn")
        c.create_oval(cx + 30, cy - 24, cx + 34, cy - 20, fill="black", tags="dyn")

        swing_arm = math.sin(walk) * 3
        c.create_polygon(cx + 12, cy, cx + 22 + swing_arm, cy + 4, cx + 18, cy + 8, fill="#1f5c31", outline="#133a1e", tags="dyn")

    def _draw_cat(self, c, cx, gy, t, color):
        if self.timer_paused:
            walk, bob, tail_swing = 0.0, 0.0, 0.0
        else:
            walk, bob, tail_swing = t * 5.0, math.sin(t * 11) * 1.5, math.sin(t * 5) * 6
        cy = gy - 24 + bob

        c.create_line(cx - 16, cy + 6, cx - 28, cy - 4 + tail_swing, fill="#d17a22", width=4, tags="dyn")

        for lx, phase in [(-10, 0), (-2, math.pi), (6, 0), (12, math.pi)]:
            swing = math.sin(walk + phase) * 5
            lby = cy + 12 + swing
            c.create_rectangle(cx + lx - 3, cy + 6, cx + lx + 3, lby + 4, fill="#e68a2e", outline="#663d14", tags="dyn")

        c.create_oval(cx - 18, cy - 10, cx + 16, cy + 14, fill="#e68a2e", outline="#663d14", width=2, tags="dyn")
        c.create_oval(cx - 6, cy, cx + 10, cy + 12, fill="#ffffff", outline="", tags="dyn")

        hx, hy = cx + 14, cy - 10
        c.create_oval(hx - 12, hy - 12, hx + 12, hy + 12, fill="#e68a2e", outline="#663d14", width=2, tags="dyn")

        c.create_polygon(hx - 10, hy - 8, hx - 12, hy - 20, hx - 2, hy - 10, fill="#e68a2e", outline="#663d14", tags="dyn")
        c.create_polygon(hx + 2, hy - 10, hx + 10, hy - 20, hx + 8, hy - 8, fill="#e68a2e", outline="#663d14", tags="dyn")

        c.create_oval(hx + 2, hy - 4, hx + 5, hy - 1, fill="#000000", tags="dyn")
        c.create_oval(hx + 4, hy + 2, hx + 10, hy + 6, fill="#ffb3b3", outline="", tags="dyn")
        c.create_line(hx + 6, hy, hx + 14, hy - 2, fill="#663d14", tags="dyn")
        c.create_line(hx + 6, hy + 3, hx + 15, hy + 3, fill="#663d14", tags="dyn")

    def _draw_dog(self, c, cx, gy, t, color):
        if self.timer_paused:
            walk, bob, ear_flop = 0.0, 0.0, 0.0
        else:
            walk, bob, ear_flop = t * 4.8, math.sin(t * 10) * 2.2, abs(math.sin(t * 8)) * 4
        cy = gy - 25 + bob

        c.create_line(cx - 16, cy + 4, cx - 26, cy - 6 + (math.sin(t*20)*5), fill="#ab825b", width=4, tags="dyn")

        for lx, phase in [(-12, 0), (-4, math.pi), (4, 0), (12, math.pi)]:
            swing = math.sin(walk + phase) * 5
            lby = cy + 12 + swing
            c.create_rectangle(cx + lx - 3, cy + 6, cx + lx + 3, lby + 4, fill="#bfa184", outline="#594330", tags="dyn")

        c.create_oval(cx - 18, cy - 10, cx + 16, cy + 14, fill="#bfa184", outline="#594330", width=2, tags="dyn")

        hx, hy = cx + 16, cy - 12
        c.create_oval(hx - 13, hy - 12, hx + 13, hy + 12, fill="#bfa184", outline="#594330", width=2, tags="dyn")

        c.create_oval(hx - 8, hy - 8 + ear_flop, hx - 1, hy + 6 + ear_flop, fill="#594330", outline="", tags="dyn")

        c.create_oval(hx + 4, hy - 4, hx + 7, hy - 1, fill="#000000", tags="dyn")
        c.create_oval(hx + 10, hy - 1, hx + 14, hy + 3, fill="#000000", tags="dyn")
        
        if not self.timer_paused:
            c.create_oval(hx + 8, hy + 4, hx + 13, hy + 9, fill="#ff6666", outline="", tags="dyn")

    @staticmethod
    def _hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(r, g, b):
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _darken(self, color, factor=0.3):
        r, g, b = self._hex_to_rgb(color)
        return self._rgb_to_hex(r * (1 - factor), g * (1 - factor), b * (1 - factor))

    def _lighten(self, color, factor=0.3):
        r, g, b = self._hex_to_rgb(color)
        return self._rgb_to_hex(
            min(255, r + (255 - r) * factor),
            min(255, g + (255 - g) * factor),
            min(255, b + (255 - b) * factor),
        )

    def _divider(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=10, padx=12)

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, font=("Malgun Gothic", 10, "bold"), bg=SIDEBAR_BG, fg=TEXT_DIM, anchor="w", padx=12).pack(fill="x", pady=(0, 4))

    def _radio_btn(self, parent, label, icon, value, variable):
        frame = tk.Frame(parent, bg=SIDEBAR_BG, padx=12)
        frame.pack(fill="x", pady=2)
        tk.Radiobutton(frame, text=f"  {icon}  {label}", variable=variable, value=value,
                       font=("Malgun Gothic", 11), bg=SIDEBAR_BG, fg=TEXT,
                       activebackground=SIDEBAR_BG, selectcolor=CARD_BG,
                       indicatoron=True, relief="flat", cursor="hand2").pack(anchor="w")

    def _entry(self, parent):
        return tk.Entry(parent, font=("Malgun Gothic", 11), bg=CARD_BG, fg=TEXT, insertbackground=TEXT,
                        relief="flat", bd=6, highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)

if __name__ == "__main__":
    app = StudyTimerApp()
    app.mainloop()