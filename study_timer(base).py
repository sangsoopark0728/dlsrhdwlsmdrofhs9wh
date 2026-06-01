#!/usr/bin/env python3
"""
📚 Study Timer App — 공부 타이머
부드러운 60fps 애니메이션 버전

처음 실행하면 자동으로 바탕화면에 실행파일(.exe / Linux 바이너리)을 빌드합니다.
이후 실행부터는 바탕화면의 앱이 바로 실행됩니다.
"""

# ══════════════════════════════════════════════════════════
#  자동 빌드 부트스트랩
#  환경변수 STUDY_TIMER_APP=1 이 없으면 빌드 모드로 진입
# ══════════════════════════════════════════════════════════
import os
import sys

_BUILT_FLAG = os.environ.get("STUDY_TIMER_APP")   # 빌드된 실행파일은 이 값이 없음
_IS_FROZEN  = getattr(sys, "frozen", False)        # PyInstaller 번들이면 True

if not _IS_FROZEN and not _BUILT_FLAG:
    # ── 이 블록은 .py 를 직접 실행했을 때만 동작 ──────────────
    import subprocess
    import shutil
    import platform

    script_path = os.path.abspath(__file__)
    script_dir  = os.path.dirname(script_path)

    # ── 바탕화면 경로 자동 감지 ──────────────────────────────
    def get_desktop_path():
        """OS별 바탕화면 경로를 반환합니다."""
        system = platform.system()

        if system == "Windows":
            # 방법 1: 레지스트리에서 읽기 (가장 정확)
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
                )
                desktop, _ = winreg.QueryValueEx(key, "Desktop")
                winreg.CloseKey(key)
                if os.path.isdir(desktop):
                    return desktop
            except Exception:
                pass
            # 방법 2: 환경변수 조합
            for env_var in ["USERPROFILE", "HOMEDRIVE", "HOMEPATH"]:
                home = os.environ.get(env_var, "")
                if home:
                    candidate = os.path.join(home, "Desktop")
                    if os.path.isdir(candidate):
                        return candidate
            # 방법 3: OneDrive 바탕화면 (한국 Windows에서 흔함)
            onedrive = os.environ.get("OneDrive", "")
            if onedrive:
                candidate = os.path.join(onedrive, "바탕 화면")
                if os.path.isdir(candidate):
                    return candidate
                candidate = os.path.join(onedrive, "Desktop")
                if os.path.isdir(candidate):
                    return candidate

        elif system == "Darwin":  # macOS
            home = os.path.expanduser("~")
            candidate = os.path.join(home, "Desktop")
            if os.path.isdir(candidate):
                return candidate

        else:  # Linux / 기타
            # XDG 표준 경로 먼저 시도
            try:
                result = subprocess.run(
                    ["xdg-user-dir", "DESKTOP"],
                    capture_output=True, text=True
                )
                candidate = result.stdout.strip()
                if candidate and os.path.isdir(candidate):
                    return candidate
            except Exception:
                pass
            home = os.path.expanduser("~")
            for name in ["Desktop", "바탕화면", "桌面"]:
                candidate = os.path.join(home, name)
                if os.path.isdir(candidate):
                    return candidate

        # 최후 fallback: 스크립트와 같은 폴더
        return script_dir

    desktop_path = get_desktop_path()

    # OS별 출력 파일명
    if platform.system() == "Windows":
        out_name = "StudyTimer.exe"
    else:
        out_name = "StudyTimer"
    out_path = os.path.join(desktop_path, out_name)

    # ── 이미 빌드된 파일이 있으면 그냥 실행 ──────────────────
    if os.path.exists(out_path):
        print(f"[StudyTimer] 실행파일 발견: {out_path}")
        print("[StudyTimer] 앱을 실행합니다...")
        if platform.system() == "Windows":
            subprocess.Popen([out_path])
            sys.exit(0)
        else:
            os.execv(out_path, [out_path])
        sys.exit(0)

    # ── 실행파일이 없으면 빌드 ────────────────────────────────
    print("=" * 60)
    print("  📚 Study Timer — 첫 실행 빌드")
    print(f"  저장 위치: {desktop_path}")
    print("  실행파일을 생성합니다. 잠시만 기다려주세요...")
    print("=" * 60)

    # 1) PyInstaller 설치 확인
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("\n[1/2] PyInstaller 설치 중...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller", "-q"],
            stdout=subprocess.DEVNULL,
        )
        print("      PyInstaller 설치 완료 ✓")

    # 2) 빌드 (임시 작업 디렉터리는 스크립트 옆에, 최종 결과물은 바탕화면으로)
    build_work = os.path.join(script_dir, "build")
    dist_temp  = os.path.join(script_dir, "_dist_temp")

    print(f"\n[2/2] 실행파일 빌드 중 → 바탕화면({desktop_path})...")
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "StudyTimer",
        "--distpath", dist_temp,   # 먼저 임시 폴더에 생성
        "--workpath", build_work,
        "--specpath", script_dir,
        "--noconfirm",
        script_path,
    ]
    result = subprocess.run(build_cmd, capture_output=True, text=True)

    temp_out = os.path.join(dist_temp, out_name)

    if result.returncode != 0 or not os.path.exists(temp_out):
        print("\n[오류] 빌드 실패. 오류 내용:")
        print(result.stderr[-2000:])
        print("\n직접 명령어로 빌드해보세요:")
        print(f"  pip install pyinstaller")
        print(f"  pyinstaller --onefile --windowed {script_path}")
        input("\nEnter 키를 눌러 종료...")
        sys.exit(1)

    # ── 바탕화면으로 이동 ─────────────────────────────────
    shutil.move(temp_out, out_path)

    # macOS: 실행 권한 부여
    if platform.system() != "Windows":
        os.chmod(out_path, 0o755)

    # 빌드 임시파일 정리
    for cleanup in [
        os.path.join(script_dir, "StudyTimer.spec"),
        build_work,
        dist_temp,
    ]:
        if os.path.isfile(cleanup):
            os.remove(cleanup)
        elif os.path.isdir(cleanup):
            shutil.rmtree(cleanup, ignore_errors=True)

    print(f"\n✅ 빌드 완료!")
    print(f"   📂 바탕화면에 저장되었습니다: {out_path}")
    print("   앱을 실행합니다...\n")

    # 3) 빌드된 실행파일 실행 (현재 프로세스 교체)
    if platform.system() == "Windows":
        subprocess.Popen([out_path])
        sys.exit(0)
    else:
        os.execv(out_path, [out_path])

    sys.exit(0)   # 여기까지 오면 안 됨

# ══════════════════════════════════════════════════════════
#  이하: 실제 앱 코드 (빌드된 실행파일 또는 개발 시 직접 실행)
# ══════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import messagebox
import math
import time

# ── 팔레트 ──────────────────────────────────────────────
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

FRAME_MS = 16   # ~60fps


# ════════════════════════════════════════════════════════
#  메인 앱
# ════════════════════════════════════════════════════════
class StudyTimerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📚 Study Timer")
        self.geometry("1100x700")
        self.minsize(900, 600)
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
        self.total_secs      = 0      # 과목 총 시간(초)
        self._start_mono     = 0.0    # monotonic 시작 시각
        self._elapsed_at_pause = 0.0  # 일시정지 시점까지 누적 경과(초)
        self._anim_id        = None   # 60fps render loop id

        # 애니메이션 내부 상태
        self.anim_w        = 800
        self.anim_h        = 140
        self.anim_ground   = 120
        self.anim_color    = ACCENT
        self.anim_start_x  = 40
        self.anim_end_x    = 760
        self.anim_progress = 0.0   # 현재 표시 진행률 (smooth)

        self._build_ui()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UI 빌드
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_ui(self):
        self._build_sidebar()
        self._build_main()

    # ── 사이드바 ─────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        logo_frame.pack(fill="x", pady=(24, 8), padx=16)
        tk.Label(logo_frame, text="📚", font=("Segoe UI Emoji", 28),
                 bg=SIDEBAR_BG, fg=TEXT).pack()
        tk.Label(logo_frame, text="Study Timer", font=("Georgia", 14, "bold"),
                 bg=SIDEBAR_BG, fg=TEXT).pack()
        tk.Label(logo_frame, text="공부 타이머", font=("Malgun Gothic", 9),
                 bg=SIDEBAR_BG, fg=TEXT_DIM).pack()

        self._divider(self.sidebar)

        self._section_label(self.sidebar, "🐾 캐릭터 선택")
        for val, label, icon in [("turtle", "거북이", "🐢"), ("rabbit", "토끼", "🐰")]:
            self._radio_btn(self.sidebar, label, icon, val, self.character)

        self._divider(self.sidebar)

        self._section_label(self.sidebar, "📦 소품 선택")
        for val, label, icon in [("box", "박스", "📦"), ("ball", "공", "⚽")]:
            self._radio_btn(self.sidebar, label, icon, val, self.prop)

        self._divider(self.sidebar)

        self._section_label(self.sidebar, "➕ 과목 추가")
        add_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG, padx=12)
        add_frame.pack(fill="x", pady=4)

        tk.Label(add_frame, text="과목명", font=("Malgun Gothic", 9),
                 bg=SIDEBAR_BG, fg=TEXT_DIM).pack(anchor="w")
        self.entry_subject = self._entry(add_frame)
        self.entry_subject.pack(fill="x", pady=(2, 6))

        tk.Label(add_frame, text="공부 시간 (분)", font=("Malgun Gothic", 9),
                 bg=SIDEBAR_BG, fg=TEXT_DIM).pack(anchor="w")
        self.entry_minutes = self._entry(add_frame)
        self.entry_minutes.pack(fill="x", pady=(2, 8))

        tk.Button(add_frame, text="+ 과목 추가", font=("Malgun Gothic", 10, "bold"),
                  bg=ACCENT, fg="#000000", activebackground="#79c0ff",
                  relief="flat", cursor="hand2", pady=6,
                  command=self._add_subject).pack(fill="x")

        bottom = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        bottom.pack(side="bottom", fill="x", padx=12, pady=16)

        self.start_btn = tk.Button(bottom, text="▶  타이머 시작",
                                   font=("Malgun Gothic", 11, "bold"),
                                   bg=SUCCESS, fg="#000000", activebackground="#56d364",
                                   relief="flat", cursor="hand2", pady=8,
                                   command=self._start_timer)
        self.start_btn.pack(fill="x", pady=(0, 6))

        tk.Button(bottom, text="↺  처음으로", font=("Malgun Gothic", 10),
                  bg=CARD_BG, fg=TEXT_DIM, activebackground=BORDER,
                  relief="flat", cursor="hand2", pady=6,
                  command=self._reset_all).pack(fill="x")

    # ── 메인 영역 ─────────────────────────────────────────
    def _build_main(self):
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self._build_schedule_view()
        self._build_timer_view()
        self.schedule_view.pack(fill="both", expand=True)

    def _build_schedule_view(self):
        self.schedule_view = tk.Frame(self.main, bg=BG)

        hdr = tk.Frame(self.schedule_view, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(32, 0))
        tk.Label(hdr, text="오늘의 공부 시간표", font=("Georgia", 22, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text="왼쪽 메뉴에서 과목을 추가하고 타이머를 시작하세요.",
                 font=("Malgun Gothic", 11), bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        list_frame = tk.Frame(self.schedule_view, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=32, pady=20)

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

    def _build_timer_view(self):
        self.timer_view = tk.Frame(self.main, bg=BG)

        top = tk.Frame(self.timer_view, bg=BG)
        top.pack(fill="x", padx=40, pady=(36, 0))
        self.lbl_subject_name = tk.Label(top, text="", font=("Georgia", 20, "bold"),
                                         bg=BG, fg=ACCENT)
        self.lbl_subject_name.pack()
        self.lbl_subject_index = tk.Label(top, text="", font=("Malgun Gothic", 11),
                                          bg=BG, fg=TEXT_DIM)
        self.lbl_subject_index.pack(pady=(2, 0))

        self.lbl_timer = tk.Label(self.timer_view, text="00:00",
                                  font=("Courier New", 72, "bold"), bg=BG, fg=TEXT)
        self.lbl_timer.pack(pady=(8, 0))

        pb_frame = tk.Frame(self.timer_view, bg=BG, padx=40)
        pb_frame.pack(fill="x", pady=(4, 0))
        self.progress_canvas = tk.Canvas(pb_frame, height=8, bg=CARD_BG,
                                         highlightthickness=0, bd=0)
        self.progress_canvas.pack(fill="x")
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 8,
                                                                   fill=ACCENT, outline="")

        anim_frame = tk.Frame(self.timer_view, bg=BG, padx=40)
        anim_frame.pack(fill="x", pady=(18, 0))
        self.anim_canvas = tk.Canvas(anim_frame, height=140, bg=CARD_BG,
                                     highlightthickness=1, bd=0,
                                     highlightbackground=BORDER)
        self.anim_canvas.pack(fill="x")
        self.anim_canvas.bind("<Configure>", self._on_canvas_resize)

        ctrl = tk.Frame(self.timer_view, bg=BG)
        ctrl.pack(pady=20)
        self.pause_btn = tk.Button(ctrl, text="⏸  일시정지",
                                   font=("Malgun Gothic", 13, "bold"),
                                   bg=WARNING, fg="#000000", activebackground="#e3b341",
                                   relief="flat", cursor="hand2", padx=24, pady=10,
                                   command=self._toggle_pause)
        self.pause_btn.pack(side="left", padx=8)
        tk.Button(ctrl, text="⏭  다음 과목", font=("Malgun Gothic", 13),
                  bg=CARD_BG, fg=TEXT, activebackground=BORDER,
                  relief="flat", cursor="hand2", padx=24, pady=10,
                  command=self._next_subject).pack(side="left", padx=8)

        self.mini_schedule = tk.Frame(self.timer_view, bg=BG)
        self.mini_schedule.pack(fill="x", padx=40, pady=(10, 0))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 과목 관리
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
            tk.Label(self.subject_list_frame,
                     text="아직 과목이 없습니다.\n왼쪽 메뉴에서 과목을 추가해주세요! ✏️",
                     font=("Malgun Gothic", 13), bg=BG, fg=TEXT_DIM, justify="center"
                     ).pack(pady=60)
            return
        for i, subj in enumerate(self.subjects):
            card = tk.Frame(self.subject_list_frame, bg=CARD_BG,
                            highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", pady=5)
            tk.Frame(card, bg=subj["color"], width=6).pack(side="left", fill="y")
            body = tk.Frame(card, bg=CARD_BG, padx=16, pady=12)
            body.pack(side="left", fill="both", expand=True)
            row1 = tk.Frame(body, bg=CARD_BG)
            row1.pack(fill="x")
            tk.Label(row1, text=f"{i+1:02d}.", font=("Courier New", 14, "bold"),
                     bg=CARD_BG, fg=subj["color"], width=3, anchor="w").pack(side="left")
            tk.Label(row1, text=subj["name"], font=("Malgun Gothic", 14, "bold"),
                     bg=CARD_BG, fg=TEXT).pack(side="left", padx=6)
            tk.Button(row1, text="✕", font=("Malgun Gothic", 10),
                      bg=CARD_BG, fg=DANGER, activebackground=CARD_BG,
                      relief="flat", cursor="hand2", bd=0,
                      command=lambda i=i: self._remove_subject(i)).pack(side="right", padx=4)
            tk.Label(body, text=f"⏱  {subj['minutes']}분", font=("Malgun Gothic", 11),
                     bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 타이머 컨트롤
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

        # 애니메이션 리셋
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
        """현재까지 누적 경과 시간(초) — 일시정지 중에는 증가하지 않음"""
        if self.timer_paused:
            return self._elapsed_at_pause
        return self._elapsed_at_pause + (time.monotonic() - self._start_mono)

    def _render_loop(self):
        """~60fps: 실제 경과 시간으로 타이머·애니메이션을 동시에 갱신"""
        if not self.timer_running:
            return

        elapsed  = self._elapsed()
        remaining = max(0.0, self.total_secs - elapsed)
        progress  = elapsed / self.total_secs if self.total_secs > 0 else 0.0
        progress  = min(progress, 1.0)

        # ── 숫자 표시 (1초 단위로 올림 처리해서 자연스럽게) ──
        remaining_ceil = math.ceil(remaining)  # 0부터 시작하지 않고 1부터 줄어들게
        mins, secs = divmod(remaining_ceil, 60)
        self.lbl_timer.configure(text=f"{mins:02d}:{secs:02d}")

        # ── 프로그레스 바 ──
        w = self.progress_canvas.winfo_width()
        if w > 0:
            self.progress_canvas.coords(self.progress_bar, 0, 0, w * progress, 8)

        # ── 애니메이션 (smooth lerp) ──
        if not self.timer_paused:
            diff = progress - self.anim_progress
            self.anim_progress += diff * 0.06   # 부드럽게 추적
        self._draw_scene(self.anim_progress)

        # ── 과목 완료 체크 ──
        if elapsed >= self.total_secs:
            self._subject_done()
            return

        self._anim_id = self.after(FRAME_MS, self._render_loop)

    def _toggle_pause(self):
        if not self.timer_running:
            return
        if not self.timer_paused:
            # 일시정지: 현재까지 경과를 저장
            self._elapsed_at_pause = self._elapsed()
            self.timer_paused = True
            self.pause_btn.configure(text="▶  재개", bg=SUCCESS)
        else:
            # 재개: monotonic 기준점 갱신
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 미니 시간표
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _refresh_mini_schedule(self, current_idx, color):
        for w in self.mini_schedule.winfo_children():
            w.destroy()
        tk.Label(self.mini_schedule, text="시간표", font=("Malgun Gothic", 10),
                 bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(0, 6))
        row = tk.Frame(self.mini_schedule, bg=BG)
        row.pack(fill="x")
        for i, subj in enumerate(self.subjects):
            if i < current_idx:
                sc, st, ab = TEXT_DIM, "✓", CARD_BG
            elif i == current_idx:
                sc, st, ab = subj["color"], "▶", CARD_BG
            else:
                sc, st, ab = BORDER, "○", BG
            pill = tk.Frame(row, bg=ab, highlightthickness=1,
                            highlightbackground=sc if i == current_idx else BORDER)
            pill.pack(side="left", padx=4, pady=2)
            tk.Label(pill, text=f"{st} {subj['name']} ({subj['minutes']}분)",
                     font=("Malgun Gothic", 9), bg=ab, fg=sc, padx=8, pady=4).pack()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 애니메이션 — 트랙 (정적 배경)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

        # 하늘 배경 그라데이션 느낌 (줄무늬)
        for i in range(0, h - 30, 4):
            t = i / (h - 30)
            r = int(0x1c + t * (0x0f - 0x1c))
            g = int(0x23 + t * (0x11 - 0x23))
            b = int(0x33 + t * (0x17 - 0x33))
            shade = f"#{r:02x}{g:02x}{b:02x}"
            c.create_line(0, i, w, i, fill=shade, tags="bg")

        # 풀밭 (바닥)
        c.create_rectangle(0, gy, w, h, fill="#1a2e1a", outline="", tags="bg")
        c.create_rectangle(0, gy, w, gy + 4, fill="#2d5a1b", outline="", tags="bg")

        # 레일 점선
        for x in range(self.anim_start_x + 20, self.anim_end_x - 20, 28):
            c.create_line(x, gy - 1, x + 14, gy - 1,
                          fill="#2d3f2d", width=2, tags="bg")

        # 시작 표시판
        sx = self.anim_start_x
        c.create_rectangle(sx - 18, gy - 32, sx + 18, gy - 10,
                            fill="#2d3748", outline=TEXT_DIM, width=1, tags="bg")
        c.create_text(sx, gy - 21, text="START",
                      fill=TEXT_DIM, font=("Courier New", 7, "bold"), tags="bg")

        # 끝 깃발
        ex = self.anim_end_x
        c.create_line(ex, gy - 50, ex, gy,
                      fill=color, width=2, tags="bg")
        c.create_polygon(ex, gy - 50,
                          ex + 22, gy - 41,
                          ex, gy - 32,
                          fill=color, outline="", tags="bg")
        c.create_text(ex, gy + 10, text="END",
                      fill=color, font=("Courier New", 7, "bold"), tags="bg")

        # 구름 장식 (고정)
        for cx_c, cy_c, r_c in [(w * 0.25, 18, 14), (w * 0.6, 12, 10), (w * 0.8, 20, 12)]:
            c.create_oval(cx_c - r_c, cy_c - r_c * 0.6,
                           cx_c + r_c, cy_c + r_c * 0.6,
                           fill="#2a3a4a", outline="", tags="bg")
            c.create_oval(cx_c - r_c * 0.5, cy_c - r_c,
                           cx_c + r_c * 0.5, cy_c + r_c * 0.2,
                           fill="#2a3a4a", outline="", tags="bg")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 애니메이션 — 매 프레임 그리기
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _draw_scene(self, progress):
        c   = self.anim_canvas
        gy  = self.anim_ground
        t   = time.time()

        travel = self.anim_end_x - self.anim_start_x
        char_x = self.anim_start_x + travel * progress

        c.delete("dyn")  # 동적 요소만 지움

        char  = self.character.get()
        prop_ = self.prop.get()
        color = self.anim_color

        # 그림자 (캐릭터 아래)
        sx = char_x
        c.create_oval(sx - 18, gy - 4, sx + 18, gy + 4,
                      fill="#0a1010", outline="", tags="dyn")

        # ── 소품 ─────────────────────────────────────────
        prop_offset = 28   # 캐릭터 앞
        px = char_x + prop_offset
        if px > self.anim_end_x + 8:
            px = self.anim_end_x + 8

        if prop_ == "box":
            self._draw_box(c, px, gy, progress, t, color)
        else:
            self._draw_ball(c, px, gy, progress, t, color)

        # ── 캐릭터 ─────────────────────────────────────────
        if char == "turtle":
            self._draw_turtle(c, char_x, gy, t, color)
        else:
            self._draw_rabbit(c, char_x, gy, t, color)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 소품: 박스
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _draw_box(self, c, px, gy, progress, t, color):
        """밀리는 박스 — 약간 앞으로 기울어지고 덜컹거리는 느낌"""
        if self.timer_paused:
            wobble = 0.0
            tilt   = 0
        else:
            # 덜컹 진동: 고주파 사인
            wobble = math.sin(t * 12) * 1.5
            tilt   = int(math.sin(t * 8) * 2)   # ±2px 기울기

        bx  = px
        by  = gy - 28 + wobble

        # 박스 측면 (3D 효과)
        c.create_polygon(bx + 14, by,
                          bx + 20, by - 6,
                          bx + 20, by + 22 - 6,
                          bx + 14, by + 22,
                          fill=self._darken(color, 0.55), outline="", tags="dyn")
        # 박스 윗면
        c.create_polygon(bx - 14, by,
                          bx + 14, by,
                          bx + 20, by - 6,
                          bx - 8,  by - 6,
                          fill=self._lighten(color, 0.3), outline="", tags="dyn")
        # 박스 정면
        c.create_rectangle(bx - 14 + tilt, by,
                            bx + 14 + tilt, by + 22,
                            fill=color, outline=self._darken(color, 0.4),
                            width=1, tags="dyn")
        # 테이프 선 (가로)
        mid_y = by + 11
        c.create_line(bx - 14 + tilt, mid_y, bx + 14 + tilt, mid_y,
                      fill=self._darken(color, 0.35), width=1, tags="dyn")
        # 테이프 선 (세로)
        c.create_line(bx + tilt, by, bx + tilt, by + 22,
                      fill=self._darken(color, 0.35), width=1, tags="dyn")
        # 박스 그림자
        c.create_oval(bx - 10, gy - 3, bx + 18, gy + 3,
                      fill="#0a1010", outline="", tags="dyn")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 소품: 공
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _draw_ball(self, c, px, gy, progress, t, color):
        """굴러가는 공 — 회전 줄무늬 + 통통 튀기기"""
        r = 14
        if self.timer_paused:
            bounce = 0.0
            angle  = 0.0
        else:
            bounce = abs(math.sin(t * 8)) * 5   # 위아래 튀기기
            angle  = t * 5.0                      # 회전 각도

        cy_ball = gy - r - bounce

        # 그림자 (찌그러짐)
        shadow_scale = 0.3 + bounce / 15
        c.create_oval(px - r * 0.9, gy - 4,
                      px + r * 0.9, gy + 3,
                      fill="#0a1010", outline="", tags="dyn")

        # 공 본체
        c.create_oval(px - r, cy_ball - r, px + r, cy_ball + r,
                      fill=color, outline=self._darken(color, 0.35),
                      width=2, tags="dyn")

        # 하이라이트
        c.create_oval(px - r * 0.5, cy_ball - r * 0.7,
                      px - r * 0.05, cy_ball - r * 0.25,
                      fill=self._lighten(color, 0.45), outline="", tags="dyn")

        # 회전 곡선 줄무늬 2개
        for offset_angle in [0, math.pi]:
            a = angle + offset_angle
            # 수직 타원형 곡선으로 회전 표현
            cx_line = px + math.sin(a) * r * 0.7
            c.create_arc(cx_line - r * 0.3, cy_ball - r,
                          cx_line + r * 0.3, cy_ball + r,
                          start=0, extent=180 if math.cos(a) >= 0 else -180,
                          style="arc",
                          outline=self._darken(color, 0.3),
                          width=1, tags="dyn")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 캐릭터: 거북이
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _draw_turtle(self, c, cx, gy, t, color):
        """귀엽고 통통한 옆면 거북이"""
        if self.timer_paused:
            walk = 0.0
            bob  = 0.0
        else:
            walk = t * 3.5         # 걷기 사이클
            bob  = math.sin(t * 7) * 1.8   # 몸통 상하

        cy = gy - 24 + bob    # 몸통 중심 Y

        # ── 꼬리 (뒤쪽) ──
        c.create_oval(cx - 26, cy - 3, cx - 14, cy + 7,
                      fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")

        # ── 뒷다리 2개 ──
        for leg_i, (lx, phase) in enumerate([(-14, 0), (-6, math.pi)]):
            swing = math.sin(walk + phase) * 6
            lby   = cy + 12 + swing
            c.create_oval(cx + lx - 7, lby - 5,
                          cx + lx + 7, lby + 5,
                          fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")
            # 발 (둥글게)
            c.create_oval(cx + lx - 5, lby + 1,
                          cx + lx + 5, lby + 8,
                          fill="#2e6b4f", outline="#1b4332", width=1, tags="dyn")

        # ── 몸통 ── (큰 타원)
        c.create_oval(cx - 22, cy - 16, cx + 22, cy + 14,
                      fill="#2d6a4f", outline="#1b4332", width=2, tags="dyn")

        # ── 등껍데기 ── (돔형)
        c.create_oval(cx - 18, cy - 20, cx + 18, cy + 6,
                      fill=color, outline=self._darken(color, 0.4), width=2, tags="dyn")
        # 껍데기 무늬 (육각형 흉내)
        sc = self._darken(color, 0.25)
        c.create_oval(cx - 8, cy - 17, cx + 8, cy - 4,
                      fill=self._darken(color, 0.15), outline=sc, width=1, tags="dyn")
        c.create_oval(cx - 14, cy - 9, cx - 3, cy + 2,
                      fill=self._darken(color, 0.15), outline=sc, width=1, tags="dyn")
        c.create_oval(cx + 3, cy - 9, cx + 14, cy + 2,
                      fill=self._darken(color, 0.15), outline=sc, width=1, tags="dyn")

        # ── 앞다리 2개 ──
        for leg_i, (lx, phase) in enumerate([(8, math.pi), (16, 0)]):
            swing = math.sin(walk + phase) * 6
            lby   = cy + 10 + swing
            c.create_oval(cx + lx - 6, lby - 5,
                          cx + lx + 6, lby + 5,
                          fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")
            c.create_oval(cx + lx - 5, lby + 1,
                          cx + lx + 5, lby + 8,
                          fill="#2e6b4f", outline="#1b4332", width=1, tags="dyn")

        # ── 목 ──
        c.create_oval(cx + 16, cy - 8, cx + 28, cy + 4,
                      fill="#40916c", outline="#1b4332", width=1, tags="dyn")

        # ── 머리 ── (귀엽게 둥글게)
        hx, hy = cx + 30, cy - 12
        c.create_oval(hx - 13, hy - 10, hx + 13, hy + 14,
                      fill="#40916c", outline="#1b4332", width=2, tags="dyn")

        # 눈 (크고 반짝이는)
        ex, ey = hx + 3, hy - 2
        c.create_oval(ex - 5, ey - 5, ex + 5, ey + 5,
                      fill="white", outline="#1b4332", width=1, tags="dyn")
        c.create_oval(ex - 2, ey - 2, ex + 3, ey + 3,
                      fill="#1a1a2e", tags="dyn")
        c.create_oval(ex - 1, ey - 4, ex + 1, ey - 2,
                      fill="white", tags="dyn")   # 반짝이

        # 입 (미소)
        c.create_arc(hx - 5, hy + 2, hx + 7, hy + 12,
                     start=200, extent=-160,
                     style="arc", outline="#1b4332", width=2, tags="dyn")

        # 코
        c.create_oval(hx + 5, hy + 2, hx + 9, hy + 5,
                      fill="#2e6b4f", outline="", tags="dyn")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 캐릭터: 토끼
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _draw_rabbit(self, c, cx, gy, t, color):
        """귀엽고 통통한 옆면 토끼"""
        if self.timer_paused:
            walk = 0.0
            bob  = 0.0
            ear_sway = 0.0
        else:
            walk     = t * 5.0
            bob      = math.sin(t * 10) * 2.5
            ear_sway = math.sin(t * 4) * 3   # 귀 흔들기

        cy = gy - 28 + bob

        # ── 꼬리 ── (뒤쪽 폭신한 공)
        c.create_oval(cx - 26, cy + 2, cx - 12, cy + 16,
                      fill="white", outline="#d0c8cc", width=1, tags="dyn")
        c.create_oval(cx - 24, cy + 4, cx - 15, cy + 14,
                      fill="#f0eaec", outline="", tags="dyn")   # 하이라이트

        # ── 뒷발 (크고 귀엽게) ──
        for lx, phase in [(-12, 0), (0, math.pi)]:
            swing = math.sin(walk + phase) * 7
            lby   = cy + 14 + swing
            c.create_oval(cx + lx - 10, lby - 4,
                          cx + lx + 10, lby + 6,
                          fill="#f0e6eb", outline="#c9b2c5", width=1, tags="dyn")
            # 발가락 암시
            for toe in [-4, 0, 4]:
                c.create_oval(cx + lx + toe - 2, lby + 3,
                              cx + lx + toe + 2, lby + 7,
                              fill="#e8d8e0", outline="", tags="dyn")

        # ── 몸통 ── (통통한 타원)
        c.create_oval(cx - 20, cy - 14, cx + 20, cy + 18,
                      fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        # 배 (밝은 부분)
        c.create_oval(cx - 10, cy - 4, cx + 12, cy + 14,
                      fill="#faf4f7", outline="", tags="dyn")

        # ── 앞발 ──
        for lx, phase in [(10, math.pi), (18, 0)]:
            swing = math.sin(walk + phase) * 5
            lby   = cy + 10 + swing
            c.create_oval(cx + lx - 7, lby - 4,
                          cx + lx + 7, lby + 5,
                          fill="#f0e6eb", outline="#c9b2c5", width=1, tags="dyn")

        # ── 머리 ── (크고 둥글게)
        hx, hy = cx + 20, cy - 20
        c.create_oval(hx - 15, hy - 12, hx + 15, hy + 15,
                      fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        # 뺨 (볼 터치)
        c.create_oval(hx + 5, hy + 3, hx + 13, hy + 11,
                      fill="#f4c2cc", outline="", tags="dyn")

        # ── 귀 (뒤쪽) ──
        ear_dx = ear_sway * 0.5
        c.create_oval(hx - 2 + ear_dx, hy - 42,
                      hx + 8 + ear_dx, hy - 12,
                      fill="#f0e8ed", outline="#c9b2c5", width=1, tags="dyn")
        c.create_oval(hx, hy - 40 + ear_dx * 0.3,
                      hx + 6, hy - 14,
                      fill=self._lighten(color, 0.2), outline="", tags="dyn")

        # ── 귀 (앞쪽) ──
        c.create_oval(hx - 12 - ear_dx, hy - 44,
                      hx - 2 - ear_dx, hy - 12,
                      fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        c.create_oval(hx - 10 - ear_dx, hy - 42,
                      hx - 4 - ear_dx, hy - 14,
                      fill=self._lighten(color, 0.2), outline="", tags="dyn")

        # ── 눈 (크고 반짝이는) ──
        ex, ey = hx + 6, hy - 4
        c.create_oval(ex - 5, ey - 5, ex + 5, ey + 5,
                      fill="white", outline="#c9b2c5", width=1, tags="dyn")
        c.create_oval(ex - 2, ey - 2, ex + 3, ey + 3,
                      fill="#2a1a2e", tags="dyn")
        c.create_oval(ex - 1, ey - 4, ex + 1, ey - 2,
                      fill="white", tags="dyn")

        # ── 코 ──
        c.create_oval(hx + 8, hy + 3, hx + 14, hy + 8,
                      fill="#f9a8c9", outline="", tags="dyn")

        # ── 수염 ──
        for wy, wlen in [(hy + 2, 12), (hy + 5, 10), (hy + 8, 11)]:
            c.create_line(hx + 8, wy, hx + 8 + wlen, wy - 1,
                          fill="#d0bcc5", width=1, tags="dyn")

        # ── 입 ──
        c.create_arc(hx + 5, hy + 6, hx + 14, hy + 14,
                     start=220, extent=-140,
                     style="arc", outline="#c9b2c5", width=1, tags="dyn")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 색상 유틸
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UI 헬퍼
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _divider(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=10, padx=12)

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, font=("Malgun Gothic", 10, "bold"),
                 bg=SIDEBAR_BG, fg=TEXT_DIM, anchor="w", padx=12).pack(fill="x", pady=(0, 4))

    def _radio_btn(self, parent, label, icon, value, variable):
        frame = tk.Frame(parent, bg=SIDEBAR_BG, padx=12)
        frame.pack(fill="x", pady=2)
        tk.Radiobutton(frame, text=f"  {icon}  {label}",
                       variable=variable, value=value,
                       font=("Malgun Gothic", 11),
                       bg=SIDEBAR_BG, fg=TEXT,
                       activebackground=SIDEBAR_BG,
                       selectcolor=CARD_BG,
                       indicatoron=True, relief="flat",
                       cursor="hand2").pack(anchor="w")

    def _entry(self, parent):
        return tk.Entry(parent, font=("Malgun Gothic", 11),
                        bg=CARD_BG, fg=TEXT, insertbackground=TEXT,
                        relief="flat", bd=6,
                        highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=ACCENT)


# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = StudyTimerApp()
    app.mainloop()
