#!/usr/bin/env python3
"""📚 Study Timer App — 공부 타이머 (리팩토링)"""

import os, sys

_BUILT_FLAG = os.environ.get("STUDY_TIMER_APP")
_IS_FROZEN  = getattr(sys, "frozen", False)

if not _IS_FROZEN and not _BUILT_FLAG:
    import subprocess, shutil, platform

    script_path = os.path.abspath(__file__)
    script_dir  = os.path.dirname(script_path)

    def get_desktop_path():
        system = platform.system()
        if system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                desktop, _ = winreg.QueryValueEx(key, "Desktop")
                winreg.CloseKey(key)
                if os.path.isdir(desktop): return desktop
            except Exception: pass
            for env_var in ["USERPROFILE", "HOMEDRIVE", "HOMEPATH"]:
                home = os.environ.get(env_var, "")
                if home:
                    c = os.path.join(home, "Desktop")
                    if os.path.isdir(c): return c
            onedrive = os.environ.get("OneDrive", "")
            if onedrive:
                for n in ["바탕 화면", "Desktop"]:
                    c = os.path.join(onedrive, n)
                    if os.path.isdir(c): return c
        elif system == "Darwin":
            c = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.isdir(c): return c
        else:
            try:
                r = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True)
                c = r.stdout.strip()
                if c and os.path.isdir(c): return c
            except Exception: pass
            home = os.path.expanduser("~")
            for name in ["Desktop", "바탕화면", "桌面"]:
                c = os.path.join(home, name)
                if os.path.isdir(c): return c
        return script_dir

    desktop_path = get_desktop_path()
    out_name = "StudyTimerProgress.exe" if platform.system() == "Windows" else "StudyTimerProgress"
    out_path = os.path.join(desktop_path, out_name)

    if os.path.exists(out_path):
        print(f"[StudyTimerProgress] 실행파일 발견: {out_path}")
        if platform.system() == "Windows":
            subprocess.Popen([out_path]); sys.exit(0)
        else:
            os.execv(out_path, [out_path]); sys.exit(0)

    print("=" * 60)
    print("  📚 Study Timer — 첫 실행 빌드")
    print(f"  저장 위치: {desktop_path}")
    print("=" * 60)

    try: import PyInstaller  # noqa
    except ImportError:
        print("\n[1/2] PyInstaller 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"],
                              stdout=subprocess.DEVNULL)

    build_work = os.path.join(script_dir, "build")
    dist_temp  = os.path.join(script_dir, "_dist_temp")

    print(f"\n[2/2] 실행파일 빌드 중 → {desktop_path}...")
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed", "--name", "StudyTimerProgress",
        "--distpath", dist_temp, "--workpath", build_work,
        "--specpath", script_dir, "--noconfirm", script_path,
    ], capture_output=True, text=True, cwd=script_dir)

    temp_out = os.path.join(dist_temp, out_name)
    if result.returncode != 0 or not os.path.exists(temp_out):
        print("\n[오류] 빌드 실패."); print(result.stderr[-2000:])
        input("\nEnter 키를 눌러 종료..."); sys.exit(1)

    shutil.move(temp_out, out_path)
    if platform.system() != "Windows": os.chmod(out_path, 0o755)

    for cleanup in [os.path.join(script_dir, "StudyTimerProgress.spec"), build_work, dist_temp]:
        if os.path.isfile(cleanup): os.remove(cleanup)
        elif os.path.isdir(cleanup): shutil.rmtree(cleanup, ignore_errors=True)

    print(f"\n✅ 빌드 완료! {out_path}")
    if platform.system() == "Windows":
        subprocess.Popen([out_path]); sys.exit(0)
    else:
        os.execv(out_path, [out_path]); sys.exit(0)

# ══════════════════════════════════════════════════════════
#  실제 앱 코드
# ══════════════════════════════════════════════════════════
import tkinter as tk
from tkinter import messagebox
import math, time, json, random

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
LIGHT_RED  = "#ff7b7b"
LIGHT_RED_HOVER = "#ff9999"

SUBJECT_COLORS = [
    "#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#ffa657",
    "#79c0ff", "#56d364", "#ff7b72", "#e3b341", "#bc8cff",
]

# ── 캐릭터/소품 메타데이터 통합 ─────────────────────────
CHARACTERS = {
    "turtle":   ("🐢", "거북이"),
    "rabbit":   ("🐰", "토끼"),
    "dinosaur": ("🦖", "공룡"),
    "dog":      ("🐶", "강아지"),
    "cat":      ("🐱", "고양이"),
}
PROPS = {
    "box":  ("📦", "박스"),
    "ball": ("⚽", "공"),
}

DAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]
DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

FRAME_MS = 16  # ~60fps


def _get_save_path():
    base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
           else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "weekly_plan.json")


# ════════════════════════════════════════════════════════
#  색상 유틸
# ════════════════════════════════════════════════════════
def _hex_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def _rgb_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def color_darken(color, factor=0.3):
    r, g, b = _hex_rgb(color)
    return _rgb_hex(r*(1-factor), g*(1-factor), b*(1-factor))

def color_lighten(color, factor=0.3):
    r, g, b = _hex_rgb(color)
    return _rgb_hex(min(255, r+(255-r)*factor),
                    min(255, g+(255-g)*factor),
                    min(255, b+(255-b)*factor))


# ════════════════════════════════════════════════════════
#  스플래시 스크린
# ════════════════════════════════════════════════════════
class SplashScreen(tk.Toplevel):
    def __init__(self, parent, on_done):
        super().__init__(parent)
        self.on_done = on_done
        self._alpha  = 0.0
        self._phase  = "in"
        self._hold_ms = 0
        total_ms = random.randint(1700, 2300)
        fade_ms  = 300
        self._hold_target = total_ms - fade_ms * 2

        self.overrideredirect(True)
        self.configure(bg="#0d1117")
        self.attributes("-alpha", 0.0)
        self.attributes("-topmost", True)

        sw, sh = parent.winfo_screenwidth(), parent.winfo_screenheight()
        w, h = 560, 380
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self._build()
        self.after(30, self._tick)

    def _build(self):
        canvas = tk.Canvas(self, bg="#0d1117", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        try:
            from PIL import Image, ImageTk
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "스터디타이머_앱_로고.png")
            img = Image.open(logo_path)
            img.thumbnail((300, 182), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            canvas.create_image(280, 165, image=self._photo, anchor="center")
        except Exception:
            canvas.create_text(280, 160, text="📚", font=("Segoe UI Emoji", 64), fill="#58a6ff")
            canvas.create_text(280, 250, text="Study Timer", font=("Georgia", 24, "bold"), fill="white")
            canvas.create_text(280, 285, text="공부 타이머", font=("Malgun Gothic", 13), fill="#8b949e")

        self._dot_canvas = tk.Canvas(self, bg="#0d1117", width=80, height=16, highlightthickness=0)
        self._dot_canvas.place(relx=0.5, rely=0.93, anchor="center")
        self._dots = [self._dot_canvas.create_oval(i*26, 2, i*26+12, 14, fill="#30363d", outline="")
                      for i in range(3)]
        self._dot_tick = 0

    def _tick(self):
        STEP = 30
        if self._phase == "in":
            self._alpha = min(1.0, self._alpha + STEP/300)
            self.attributes("-alpha", self._alpha)
            if self._alpha >= 1.0: self._phase = "hold"
            self.after(STEP, self._tick)
        elif self._phase == "hold":
            self._hold_ms += STEP
            active = (self._dot_tick // 4) % 3
            for i, dot in enumerate(self._dots):
                self._dot_canvas.itemconfigure(dot, fill="#58a6ff" if i == active else "#30363d")
            self._dot_tick += 1
            if self._hold_ms >= self._hold_target: self._phase = "out"
            self.after(STEP, self._tick)
        elif self._phase == "out":
            self._alpha = max(0.0, self._alpha - STEP/300)
            self.attributes("-alpha", self._alpha)
            if self._alpha <= 0.0:
                self.destroy(); self.on_done(); return
            self.after(STEP, self._tick)


# ════════════════════════════════════════════════════════
#  공통 다이얼로그
# ════════════════════════════════════════════════════════
class StyledDialog(tk.Toplevel):
    def __init__(self, parent, title, message, buttons, icon="❓"):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        w, h = 480, 280
        parent.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()//2 - w//2
        py = parent.winfo_rooty() + parent.winfo_height()//2 - h//2
        self.geometry(f"{w}x{h}+{px}+{py}")

        card = tk.Frame(tk.Frame(self, bg=BG), bg=CARD_BG,
                        highlightthickness=1, highlightbackground=BORDER)
        card.master.pack(fill="both", expand=True, padx=2, pady=2)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(card, text=icon, font=("Segoe UI Emoji", 36), bg=CARD_BG, fg=ACCENT).pack(pady=(20, 6))
        tk.Label(card, text=title, font=("Georgia", 14, "bold"), bg=CARD_BG, fg=TEXT).pack()
        tk.Label(card, text=message, font=("Malgun Gothic", 11), bg=CARD_BG, fg=TEXT_DIM,
                 justify="center", wraplength=400).pack(pady=(10, 18), padx=20)

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.pack(pady=(0, 20))
        for label, color, value in buttons:
            tk.Button(btn_frame, text=label, font=("Malgun Gothic", 11, "bold"),
                      bg=color, fg="#000000",
                      activebackground=color_lighten(color, 0.12),
                      relief="flat", cursor="hand2", padx=22, pady=8, bd=0,
                      command=lambda v=value: self._close(v)).pack(side="left", padx=6)

        self.protocol("WM_DELETE_WINDOW", lambda: self._close(None))
        self.wait_window()

    def _close(self, value):
        self.result = value
        self.destroy()


# ════════════════════════════════════════════════════════
#  메인 앱
# ════════════════════════════════════════════════════════
class StudyTimerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📚 Study Timer Progress")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(bg=BG)

        self.subjects     = []
        self.weekly_plan  = {k: [] for k in DAY_KEYS}
        self.character    = tk.StringVar(value="turtle")
        self.prop         = tk.StringVar(value="box")
        self.current_tab  = tk.StringVar(value="today")
        self.selected_day = tk.StringVar(value="mon")

        self.timer_running     = False
        self.timer_paused      = False
        self.current_subject   = 0
        self.total_secs        = 0
        self._start_mono       = 0.0
        self._elapsed_at_pause = 0.0
        self._anim_id          = None

        self.anim_w        = 800
        self.anim_h        = 140
        self.anim_ground   = 120
        self.anim_color    = ACCENT
        self.anim_start_x  = 40
        self.anim_end_x    = 760
        self.anim_progress = 0.0

        self._load_weekly_plan()
        self._build_ui()
        # 불러온 오늘의 과목 리스트를 UI에 반영
        self._refresh_subject_list()
        # 앱 종료 시 자동 저장
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._show_splash()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 저장 / 불러오기
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _load_weekly_plan(self):
        try:
            with open(_get_save_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return
            # 주간 계획 불러오기
            for k in DAY_KEYS:
                if k in data and isinstance(data[k], list):
                    self.weekly_plan[k] = data[k]
            # 오늘의 공부 시간표 불러오기
            if "today_subjects" in data and isinstance(data["today_subjects"], list):
                self.subjects = data["today_subjects"]
                # 누락 필드 보정
                for i, s in enumerate(self.subjects):
                    if "color" not in s:
                        s["color"] = SUBJECT_COLORS[i % len(SUBJECT_COLORS)]
                    s.setdefault("elapsed_secs", 0.0)
                    s.setdefault("completed", False)
                    s.setdefault("character", "turtle")
                    s.setdefault("prop", "box")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_weekly_plan(self):
        try:
            data = {k: self.weekly_plan[k] for k in DAY_KEYS}
            data["today_subjects"] = self.subjects
            with open(_get_save_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[저장 오류] {e}")

    def _on_close(self):
        """앱 종료 시 현재 진행도까지 포함해 저장"""
        try:
            if self.timer_running:
                self._save_current_progress()
                self._stop_loops()
            self._save_weekly_plan()
        except Exception as e:
            print(f"[종료 저장 오류] {e}")
        self.destroy()

    def _show_splash(self):
        self.withdraw()
        SplashScreen(self, on_done=self.deiconify)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UI 빌드
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_ui(self):
        self._build_sidebar()
        self._build_main()

    # ── 사이드바 ────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        logo.pack(fill="x", pady=(24, 8), padx=16)
        tk.Label(logo, text="📚", font=("Segoe UI Emoji", 28), bg=SIDEBAR_BG, fg=TEXT).pack()
        tk.Label(logo, text="Study Timer", font=("Georgia", 14, "bold"), bg=SIDEBAR_BG, fg=TEXT).pack()
        tk.Label(logo, text="공부 타이머", font=("Malgun Gothic", 9), bg=SIDEBAR_BG, fg=TEXT_DIM).pack()

        self._divider(self.sidebar)
        self._section_label(self.sidebar, "🐾 캐릭터 선택")
        for key, (icon, label) in CHARACTERS.items():
            self._radio_btn(self.sidebar, label, icon, key, self.character)

        self._divider(self.sidebar)
        self._section_label(self.sidebar, "📦 소품 선택")
        for key, (icon, label) in PROPS.items():
            self._radio_btn(self.sidebar, label, icon, key, self.prop)

        self._divider(self.sidebar)
        self.sidebar_add_frame = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        self.sidebar_add_frame.pack(fill="x")
        self._rebuild_sidebar_add()
        self.current_tab.trace_add("write", lambda *_: self._rebuild_sidebar_add())
        self.selected_day.trace_add("write", lambda *_: self._rebuild_sidebar_add())
        self.character.trace_add("write", lambda *_: self._update_preview())
        self.prop.trace_add("write", lambda *_: self._update_preview())

    def _rebuild_sidebar_add(self):
        for w in self.sidebar_add_frame.winfo_children(): w.destroy()
        tab = self.current_tab.get()

        if tab == "today":
            self._section_label(self.sidebar_add_frame, "➕ 과목 추가 (오늘)")
        else:
            self._section_label(self.sidebar_add_frame, "➕ 과목 추가 (주간)")
            day_frame = tk.Frame(self.sidebar_add_frame, bg=SIDEBAR_BG, padx=12)
            day_frame.pack(fill="x", pady=(0, 6))
            tk.Label(day_frame, text="요일 선택", font=("Malgun Gothic", 9),
                     bg=SIDEBAR_BG, fg=TEXT_DIM).pack(anchor="w", pady=(0, 4))
            rows = [tk.Frame(day_frame, bg=SIDEBAR_BG) for _ in range(2)]
            for r in rows: r.pack(fill="x", pady=(0, 2))
            for i, (dk, kr) in enumerate(zip(DAY_KEYS, DAYS_KR)):
                is_sel = self.selected_day.get() == dk
                tk.Button(rows[0 if i < 4 else 1], text=kr,
                          font=("Malgun Gothic", 10, "bold"),
                          bg=ACCENT if is_sel else CARD_BG,
                          fg="#000000" if is_sel else TEXT_DIM,
                          activebackground=ACCENT, relief="flat", cursor="hand2",
                          padx=8, pady=4, bd=0, width=3,
                          command=lambda d=dk: self.selected_day.set(d)).pack(side="left", padx=1)

        add = tk.Frame(self.sidebar_add_frame, bg=SIDEBAR_BG, padx=12)
        add.pack(fill="x", pady=4)
        for lbl, attr in [("과목명", "entry_subject"), ("공부 시간 (분)", "entry_minutes")]:
            tk.Label(add, text=lbl, font=("Malgun Gothic", 9), bg=SIDEBAR_BG, fg=TEXT_DIM).pack(anchor="w")
            entry = self._entry(add)
            entry.pack(fill="x", pady=(2, 6))
            setattr(self, attr, entry)

        self.preview_label = tk.Label(add, text="", font=("Malgun Gothic", 9),
                                      bg=SIDEBAR_BG, fg=TEXT_DIM, justify="left")
        self.preview_label.pack(anchor="w", pady=(0, 6))
        self._update_preview()

        if tab == "today":
            tk.Button(add, text="+ 과목 추가", font=("Malgun Gothic", 10, "bold"),
                      bg=ACCENT, fg="#000000", activebackground="#79c0ff",
                      relief="flat", cursor="hand2", pady=6,
                      command=self._add_subject).pack(fill="x")
        else:
            tk.Label(add, text="↘ 아래 버튼으로 추가하세요",
                     font=("Malgun Gothic", 9), bg=SIDEBAR_BG, fg=TEXT_DIM).pack(anchor="w")

    def _update_preview(self):
        if not hasattr(self, "preview_label"): return
        c_icon, c_label = CHARACTERS.get(self.character.get(), ("", ""))
        p_icon, p_label = PROPS.get(self.prop.get(), ("", ""))
        self.preview_label.configure(
            text=f"포함:  {c_icon} {c_label}  +  {p_icon} {p_label}")

    # ── 메인 영역 ────────────────────────────────────────
    def _build_main(self):
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self._build_tab_header()
        self._build_today_view()
        self._build_weekly_view()
        self._build_timer_view()
        self._switch_tab("today")

    def _build_tab_header(self):
        self.tab_header = tk.Frame(self.main, bg=SIDEBAR_BG, height=50)
        self.tab_header.pack(fill="x")
        self.tab_header.pack_propagate(False)
        inner = tk.Frame(self.tab_header, bg=SIDEBAR_BG)
        inner.pack(side="left", padx=24, pady=8)

        self.tab_today_btn = tk.Button(inner, text="📅  오늘의 공부 시간표",
            font=("Malgun Gothic", 11, "bold"), bg=ACCENT, fg="#000000",
            activebackground="#79c0ff", relief="flat", cursor="hand2",
            padx=18, pady=6, bd=0, command=lambda: self._switch_tab("today"))
        self.tab_today_btn.pack(side="left", padx=(0, 6))

        self.tab_weekly_btn = tk.Button(inner, text="🗓  주간 계획표",
            font=("Malgun Gothic", 11, "bold"), bg=CARD_BG, fg=TEXT_DIM,
            activebackground=BORDER, relief="flat", cursor="hand2",
            padx=18, pady=6, bd=0, command=lambda: self._switch_tab("weekly"))
        self.tab_weekly_btn.pack(side="left")

    def _switch_tab(self, tab):
        self.current_tab.set(tab)
        is_today = tab == "today"
        self.tab_today_btn.configure(bg=ACCENT if is_today else CARD_BG,
                                     fg="#000000" if is_today else TEXT_DIM)
        self.tab_weekly_btn.configure(bg=CARD_BG if is_today else ACCENT,
                                      fg=TEXT_DIM if is_today else "#000000")
        for v in [getattr(self, n, None) for n in ("today_view", "weekly_view", "timer_view")]:
            if v: v.pack_forget()
        if is_today:
            self.today_view.pack(fill="both", expand=True)
        else:
            self.weekly_view.pack(fill="both", expand=True)
            self._refresh_weekly_view()

    # ── 오늘의 공부 시간표 뷰 ───────────────────────────
    def _build_today_view(self):
        self.today_view = tk.Frame(self.main, bg=BG)
        hdr = tk.Frame(self.today_view, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(24, 0))
        tk.Label(hdr, text="오늘의 공부 시간표",
                 font=("Georgia", 22, "bold"), bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text="왼쪽 메뉴에서 과목을 추가하고 타이머를 시작하세요.",
                 font=("Malgun Gothic", 11), bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        list_frame = tk.Frame(self.today_view, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=32, pady=16)
        canvas = tk.Canvas(list_frame, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.subject_list_frame = tk.Frame(canvas, bg=BG)
        self.subject_list_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.subject_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        tk.Label(self.subject_list_frame,
                 text="아직 과목이 없습니다.\n왼쪽 메뉴에서 과목을 추가해주세요! ✏️",
                 font=("Malgun Gothic", 13), bg=BG, fg=TEXT_DIM, justify="center").pack(pady=60)

        bottom = tk.Frame(self.today_view, bg=BG)
        bottom.pack(fill="x", padx=32, pady=(0, 20))
        self.start_btn = tk.Button(bottom, text="▶  타이머 시작",
            font=("Malgun Gothic", 15, "bold"), bg=LIGHT_RED, fg="#000000",
            activebackground=LIGHT_RED_HOVER, relief="flat", cursor="hand2",
            padx=32, pady=16, bd=0, command=self._start_timer)
        self.start_btn.pack(side="right")
        tk.Button(bottom, text="오늘 공부 기록 초기화",
                  font=("Malgun Gothic", 12, "bold"), bg=CARD_BG, fg=TEXT,
                  activebackground=BORDER, relief="flat", cursor="hand2",
                  padx=22, pady=14, bd=0,
                  command=self._reset_today_progress).pack(side="right", padx=(0, 10))
    # ── 주간 계획표 뷰 ──────────────────────────────────
    def _build_weekly_view(self):
        self.weekly_view = tk.Frame(self.main, bg=BG)
        hdr = tk.Frame(self.weekly_view, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(24, 0))
        tk.Label(hdr, text="주간 계획표",
                 font=("Georgia", 22, "bold"), bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(hdr, text="요일별로 과목과 시간을 계획해보세요. 왼쪽에서 과목명/시간을 입력 후 아래 버튼을 누르세요.",
                 font=("Malgun Gothic", 11), bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(4, 0))

        day_tab_frame = tk.Frame(self.weekly_view, bg=BG)
        day_tab_frame.pack(fill="x", padx=32, pady=(16, 0))
        self.day_tab_buttons = {}
        for dk, kr in zip(DAY_KEYS, DAYS_KR):
            btn = tk.Button(day_tab_frame, text=kr,
                font=("Malgun Gothic", 12, "bold"), bg=CARD_BG,
                fg="#ff6b6b" if dk in ("sat", "sun") else TEXT_DIM,
                activebackground=BORDER, relief="flat", cursor="hand2",
                padx=14, pady=8, bd=0, width=4,
                command=lambda d=dk: self._select_weekly_day(d))
            btn.pack(side="left", padx=3)
            self.day_tab_buttons[dk] = btn

        tk.Frame(self.weekly_view, bg=BORDER, height=1).pack(fill="x", padx=32, pady=(8, 0))

        self.weekly_content_frame = tk.Frame(self.weekly_view, bg=BG)
        self.weekly_content_frame.pack(fill="both", expand=True, padx=32, pady=(12, 0))

        bottom = tk.Frame(self.weekly_view, bg=BG)
        bottom.pack(fill="x", padx=32, pady=(8, 20))
        tk.Button(bottom, text="➕  과목 추가",
                  font=("Malgun Gothic", 14, "bold"), bg=ACCENT, fg="#000000",
                  activebackground="#79c0ff", relief="flat", cursor="hand2",
                  padx=28, pady=14, bd=0, command=self._add_subject).pack(side="right")
        tk.Button(bottom, text="오늘 공부로 불러오기",
                  font=("Malgun Gothic", 12, "bold"), bg=CARD_BG, fg=TEXT,
                  activebackground=BORDER, relief="flat", cursor="hand2",
                  padx=22, pady=14, bd=0,
                  command=self._load_weekly_day_to_today).pack(side="right", padx=(0, 10))

        self._select_weekly_day("mon")

    def _select_weekly_day(self, day_key):
        self.selected_day.set(day_key)
        if hasattr(self, "day_tab_buttons"):
            for dk, btn in self.day_tab_buttons.items():
                is_weekend = dk in ("sat", "sun")
                btn.configure(bg=ACCENT if dk == day_key else CARD_BG,
                               fg="#000000" if dk == day_key
                               else ("#ff6b6b" if is_weekend else TEXT_DIM))
        self._refresh_weekly_day_content(day_key)

    def _refresh_weekly_view(self):
        self._select_weekly_day(self.selected_day.get())

    def _refresh_weekly_day_content(self, day_key=None):
        if day_key is None: day_key = self.selected_day.get()
        for w in self.weekly_content_frame.winfo_children(): w.destroy()

        kr_label = DAYS_KR[DAY_KEYS.index(day_key)]
        day_hdr = tk.Frame(self.weekly_content_frame, bg=BG)
        day_hdr.pack(fill="x", pady=(0, 12))
        day_color = "#ff6b6b" if day_key in ("sat", "sun") else ACCENT
        tk.Label(day_hdr, text=f"{kr_label}요일 계획",
                 font=("Georgia", 16, "bold"), bg=BG, fg=day_color).pack(side="left")

        day_subjects = self.weekly_plan.get(day_key, [])
        total_min = sum(s["minutes"] for s in day_subjects)
        if total_min > 0:
            h, m = divmod(total_min, 60)
            tk.Label(day_hdr, text=f"  총 {h}시간 {m}분" if h else f"  총 {m}분",
                     font=("Malgun Gothic", 11), bg=BG, fg=TEXT_DIM).pack(side="left", padx=12)

        inner = self._scrollable_frame(self.weekly_content_frame)
        if not day_subjects:
            tk.Label(inner,
                text=f"아직 {kr_label}요일 계획이 없습니다.\n왼쪽에서 과목명/시간을 입력하고 오른쪽 아래 버튼을 눌러 추가하세요! 📝",
                font=("Malgun Gothic", 12), bg=BG, fg=TEXT_DIM, justify="center").pack(pady=50)
            return

        for i, subj in enumerate(day_subjects):
            card, body = self._subject_card(inner, subj, i)
            row1, _ = self._card_row1(body, subj, i)
            tk.Button(row1, text="✕", font=("Malgun Gothic", 10),
                      bg=CARD_BG, fg=DANGER, activebackground=CARD_BG,
                      relief="flat", cursor="hand2", bd=0,
                      command=lambda dk=day_key, idx=i: self._remove_weekly_subject(dk, idx)
                      ).pack(side="right", padx=4)
            row2 = tk.Frame(body, bg=CARD_BG)
            row2.pack(fill="x", pady=(6, 0))
            tk.Label(row2, text=f"⏱  {subj['minutes']}분",
                     font=("Malgun Gothic", 11), bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
            tk.Label(row2, text="  │  ", font=("Malgun Gothic", 11),
                     bg=CARD_BG, fg=BORDER).pack(side="left")
            self._char_prop_badges(row2, subj)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 공통 카드 빌더 헬퍼
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _scrollable_frame(self, parent):
        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        return inner

    def _subject_card(self, parent, subj, idx):
        card = tk.Frame(parent, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", pady=5, padx=2)
        tk.Frame(card, bg=subj["color"], width=6).pack(side="left", fill="y")
        body = tk.Frame(card, bg=CARD_BG, padx=16, pady=12)
        body.pack(side="left", fill="both", expand=True)
        return card, body

    def _card_row1(self, body, subj, idx):
        row1 = tk.Frame(body, bg=CARD_BG)
        row1.pack(fill="x")
        tk.Label(row1, text=f"{idx+1:02d}.", font=("Courier New", 14, "bold"),
                 bg=CARD_BG, fg=subj["color"], width=3, anchor="w").pack(side="left")
        name_lbl = tk.Label(row1, text=subj["name"],
                            font=("Malgun Gothic", 14, "bold"), bg=CARD_BG, fg=TEXT)
        name_lbl.pack(side="left", padx=6)
        return row1, name_lbl

    def _char_prop_badges(self, parent, subj):
        for meta_dict, key_name in [(CHARACTERS, "character"), (PROPS, "prop")]:
            key = subj.get(key_name, list(meta_dict.keys())[0])
            icon, label = meta_dict.get(key, ("", key))
            tk.Label(parent, text=f"{icon} {label}", font=("Malgun Gothic", 10),
                     bg=color_darken(subj["color"], 0.65),
                     fg=subj["color"], padx=8, pady=2).pack(side="left", padx=(0, 4))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 과목 관리
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _add_subject(self):
        name = self.entry_subject.get().strip()
        mins = self.entry_minutes.get().strip()
        if not name:
            messagebox.showwarning("입력 오류", "과목명을 입력해주세요."); return
        if not mins.isdigit():
            messagebox.showwarning("입력 오류", "숫자만 입력해주세요."); return
        mins = int(mins)
        if mins <= 0:
            messagebox.showwarning("입력 오류", "1 이상의 숫자를 입력해주세요."); return

        subj_data = {
            "name": name, "minutes": mins,
            "character": self.character.get(), "prop": self.prop.get(),
        }
        if self.current_tab.get() == "today":
            subj_data.update({"elapsed_secs": 0.0, "completed": False,
                              "color": SUBJECT_COLORS[len(self.subjects) % len(SUBJECT_COLORS)]})
            self.subjects.append(subj_data)
            self._save_weekly_plan()
            self._refresh_subject_list()
        else:
            day_key = self.selected_day.get()
            day_subjects = self.weekly_plan[day_key]
            subj_data["color"] = SUBJECT_COLORS[len(day_subjects) % len(SUBJECT_COLORS)]
            day_subjects.append(subj_data)
            self._save_weekly_plan()
            self._refresh_weekly_day_content(day_key)

        self.entry_subject.delete(0, "end")
        self.entry_minutes.delete(0, "end")

    def _reset_today_progress(self):
        if self.timer_running:
            messagebox.showinfo("안내", "타이머 실행 중에는 기록을 초기화할 수 없습니다.")
            return
        if not self.subjects:
            messagebox.showinfo("안내", "초기화할 오늘 공부 과목이 없습니다.")
            return
        for subj in self.subjects:
            subj["elapsed_secs"] = 0.0
            subj["completed"] = False
        self._save_weekly_plan()
        self._refresh_subject_list()
        messagebox.showinfo("초기화 완료", "오늘 공부 과목은 그대로 두고 진행도만 초기화했습니다.")

    def _load_weekly_day_to_today(self):
        if self.timer_running:
            messagebox.showinfo("안내", "타이머 실행 중에는 주간 계획을 불러올 수 없습니다.")
            return
        day_key = self.selected_day.get()
        day_subjects = self.weekly_plan.get(day_key, [])
        if not day_subjects:
            messagebox.showinfo("안내", "선택한 요일에 불러올 계획이 없습니다.")
            return
        imported = []
        for src in day_subjects:
            if not isinstance(src, dict):
                continue
            try:
                minutes = int(src.get("minutes", 0))
            except (TypeError, ValueError):
                continue
            if minutes <= 0:
                continue
            imported.append({
                "name": src.get("name", ""),
                "minutes": minutes,
                "color": SUBJECT_COLORS[len(imported) % len(SUBJECT_COLORS)],
                "character": src.get("character", "turtle"),
                "prop": src.get("prop", "box"),
                "elapsed_secs": 0.0,
                "completed": False,
            })
        if not imported:
            messagebox.showinfo("안내", "불러올 수 있는 과목이 없습니다.")
            return
        self.subjects = imported
        self._save_weekly_plan()
        self._refresh_subject_list()
        self._switch_tab("today")
        messagebox.showinfo("불러오기 완료", "선택한 주간 계획을 오늘 공부로 불러왔습니다.")

    def _remove_subject(self, idx):
        if self.timer_running:
            messagebox.showinfo("안내", "타이머 실행 중에는 과목을 삭제할 수 없습니다."); return
        self.subjects.pop(idx)
        for i, s in enumerate(self.subjects):
            s["color"] = SUBJECT_COLORS[i % len(SUBJECT_COLORS)]
        self._save_weekly_plan()
        self._refresh_subject_list()

    def _remove_weekly_subject(self, day_key, idx):
        self.weekly_plan[day_key].pop(idx)
        for i, s in enumerate(self.weekly_plan[day_key]):
            s["color"] = SUBJECT_COLORS[i % len(SUBJECT_COLORS)]
        self._save_weekly_plan()
        self._refresh_weekly_day_content(day_key)

    def _refresh_subject_list(self):
        for w in self.subject_list_frame.winfo_children(): w.destroy()
        if not self.subjects:
            tk.Label(self.subject_list_frame,
                     text="아직 과목이 없습니다.\n왼쪽 메뉴에서 과목을 추가해주세요! ✏️",
                     font=("Malgun Gothic", 13), bg=BG, fg=TEXT_DIM, justify="center").pack(pady=60)
            return

        for i, subj in enumerate(self.subjects):
            _, body = self._subject_card(self.subject_list_frame, subj, i)
            row1, _ = self._card_row1(body, subj, i)
            tk.Button(row1, text="✕", font=("Malgun Gothic", 10),
                      bg=CARD_BG, fg=DANGER, activebackground=CARD_BG,
                      relief="flat", cursor="hand2", bd=0,
                      command=lambda i=i: self._remove_subject(i)).pack(side="right", padx=4)

            row2 = tk.Frame(body, bg=CARD_BG)
            row2.pack(fill="x", pady=(6, 0))
            elapsed = float(subj.get("elapsed_secs", 0.0))
            progress = 1.0 if subj.get("completed") else min(elapsed / max(1, subj["minutes"]*60), 1.0)
            status = "완료" if subj.get("completed") else f"{int(progress*100)}%"
            tk.Label(row2, text=f"⏱  {subj['minutes']}분",
                     font=("Malgun Gothic", 11), bg=CARD_BG, fg=TEXT_DIM).pack(side="left")
            tk.Label(row2, text=f"  진행도 {status}",
                     font=("Malgun Gothic", 11), bg=CARD_BG,
                     fg=SUCCESS if subj.get("completed") else TEXT_DIM).pack(side="left")
            tk.Label(row2, text="  │  ", font=("Malgun Gothic", 11),
                     bg=CARD_BG, fg=BORDER).pack(side="left")
            self._char_prop_badges(row2, subj)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 타이머 뷰
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _build_timer_view(self):
        self.timer_view = tk.Frame(self.main, bg=BG)

        top_bar = tk.Frame(self.timer_view, bg=BG)
        top_bar.pack(fill="x", padx=24, pady=(16, 0))
        tk.Button(top_bar, text="🏠  메인화면",
                  font=("Malgun Gothic", 10, "bold"), bg=CARD_BG, fg=TEXT,
                  activebackground=BORDER, relief="flat", cursor="hand2",
                  padx=14, pady=6, bd=0, command=self._go_main_from_timer).pack(side="left")

        top = tk.Frame(self.timer_view, bg=BG)
        top.pack(fill="x", padx=40, pady=(16, 0))
        self.lbl_subject_name  = tk.Label(top, text="", font=("Georgia", 20, "bold"), bg=BG, fg=ACCENT)
        self.lbl_subject_name.pack()
        self.lbl_subject_index = tk.Label(top, text="", font=("Malgun Gothic", 11), bg=BG, fg=TEXT_DIM)
        self.lbl_subject_index.pack(pady=(2, 0))
        self.lbl_char_prop     = tk.Label(top, text="", font=("Malgun Gothic", 13), bg=BG, fg=TEXT_DIM)
        self.lbl_char_prop.pack(pady=(2, 0))

        self.lbl_timer = tk.Label(self.timer_view, text="00:00",
                                  font=("Courier New", 72, "bold"), bg=BG, fg=TEXT)
        self.lbl_timer.pack(pady=(8, 0))

        pb_frame = tk.Frame(self.timer_view, bg=BG, padx=40)
        pb_frame.pack(fill="x", pady=(4, 0))
        self.progress_canvas = tk.Canvas(pb_frame, height=8, bg=CARD_BG, highlightthickness=0, bd=0)
        self.progress_canvas.pack(fill="x")
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 8, fill=ACCENT, outline="")

        anim_frame = tk.Frame(self.timer_view, bg=BG, padx=40)
        anim_frame.pack(fill="x", pady=(18, 0))
        self.anim_canvas = tk.Canvas(anim_frame, height=140, bg=CARD_BG,
                                     highlightthickness=1, bd=0, highlightbackground=BORDER)
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
    # 타이머 컨트롤
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _start_timer(self):
        if not self.subjects:
            messagebox.showwarning("과목 없음", "먼저 과목을 추가해주세요."); return
        start_idx = self._first_pending_subject_index()
        if start_idx is None:
            messagebox.showinfo("완료", "모든 과목이 이미 완료되었습니다."); return
        self.timer_running = True
        self.timer_paused  = False
        self.current_subject = start_idx
        self.today_view.pack_forget()
        self.tab_header.pack_forget()
        self.timer_view.pack(fill="both", expand=True)
        self._load_subject(start_idx)

    def _load_subject(self, idx):
        if idx >= len(self.subjects): self._all_done(); return
        self.current_subject   = idx
        subj                   = self.subjects[idx]
        self.total_secs        = subj["minutes"] * 60
        self._elapsed_at_pause = min(float(subj.get("elapsed_secs", 0.0)), self.total_secs)
        self._start_mono       = time.monotonic()

        color = subj["color"]
        self.character.set(subj.get("character", "turtle"))
        self.prop.set(subj.get("prop", "box"))

        self.lbl_subject_name.configure(text=subj["name"], fg=color)
        self.lbl_subject_index.configure(text=f"과목 {idx+1} / {len(self.subjects)}")
        self.lbl_timer.configure(fg=color)
        self.progress_canvas.itemconfigure(self.progress_bar, fill=color)
        self._refresh_mini_schedule(idx, color)

        c_icon, c_label = CHARACTERS.get(self.character.get(), ("", ""))
        p_icon, p_label = PROPS.get(self.prop.get(), ("", ""))
        self.lbl_char_prop.configure(text=f"{c_icon} {c_label}  +  {p_icon} {p_label}", fg=color)

        self.anim_progress = self._elapsed_at_pause / self.total_secs if self.total_secs else 0.0
        self.anim_color    = color
        self._rebuild_track()
        self._stop_loops()
        self._render_loop()

    def _stop_loops(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None

    def _elapsed(self):
        if self.timer_paused: return self._elapsed_at_pause
        return self._elapsed_at_pause + (time.monotonic() - self._start_mono)

    def _save_current_progress(self):
        if not self.subjects or self.current_subject >= len(self.subjects): return
        subj = self.subjects[self.current_subject]
        elapsed = min(self._elapsed(), subj["minutes"] * 60)
        subj["elapsed_secs"] = elapsed
        subj["completed"]    = elapsed >= subj["minutes"] * 60

    def _first_pending_subject_index(self):
        return next((i for i, s in enumerate(self.subjects) if not s.get("completed")), None)

    def _show_today_view(self):
        self._stop_loops()
        self.timer_running = self.timer_paused = False
        self.timer_view.pack_forget()
        self.tab_header.pack(fill="x")
        self._switch_tab("today")
        self.pause_btn.configure(text="⏸  일시정지", bg=WARNING, state="normal")
        self._save_weekly_plan()
        self._refresh_subject_list()

    def _render_loop(self):
        if not self.timer_running: return
        elapsed   = self._elapsed()
        self._save_current_progress()
        remaining = max(0.0, self.total_secs - elapsed)
        progress  = min(elapsed / self.total_secs if self.total_secs else 0.0, 1.0)

        mins, secs = divmod(math.ceil(remaining), 60)
        self.lbl_timer.configure(text=f"{mins:02d}:{secs:02d}")

        w = self.progress_canvas.winfo_width()
        if w > 0: self.progress_canvas.coords(self.progress_bar, 0, 0, w * progress, 8)

        if not self.timer_paused:
            self.anim_progress += (progress - self.anim_progress) * 0.06
        self._draw_scene(self.anim_progress)

        if elapsed >= self.total_secs: self._subject_done(); return
        self._anim_id = self.after(FRAME_MS, self._render_loop)

    def _toggle_pause(self):
        if not self.timer_running: return
        if not self.timer_paused:
            self._elapsed_at_pause = self._elapsed()
            self.timer_paused = True
            self.pause_btn.configure(text="▶  재개", bg=SUCCESS)
            self._save_weekly_plan()
        else:
            self._start_mono  = time.monotonic()
            self.timer_paused = False
            self.pause_btn.configure(text="⏸  일시정지", bg=WARNING)
            self._render_loop()

    def _next_subject(self):
        self._stop_loops()
        self._save_current_progress()
        self._save_weekly_plan()
        self._load_subject(self.current_subject + 1)

    def _subject_done(self):
        self._stop_loops()
        self._elapsed_at_pause = self.total_secs
        self._save_current_progress()
        self._save_weekly_plan()
        self.lbl_timer.configure(text="완료! ✓")
        self.anim_progress = 1.0
        self._draw_scene(1.0)

        next_idx = self.current_subject + 1
        if next_idx >= len(self.subjects):
            self.after(800, self._all_done); return

        def ask_next():
            dlg = StyledDialog(self, title="다음 과목", message="다음 과목을 시작하시겠습니까?",
                               buttons=[("예", SUCCESS, "yes"), ("아니오", CARD_BG, "no")], icon="⏭")
            if dlg.result == "yes": self._load_subject(next_idx)
            else: self._show_today_view()
        self.after(800, ask_next)

    def _go_main_from_timer(self):
        was_paused = self.timer_paused
        if self.timer_running and not self.timer_paused:
            self._elapsed_at_pause = self._elapsed()
            self.timer_paused = True
            self._stop_loops()
        dlg = StyledDialog(self, title="메인화면으로 돌아가기",
                           message="현재 과목의 진행도를 저장하고 메인화면으로 돌아가시겠습니까?",
                           buttons=[("예", LIGHT_RED, "yes"), ("아니오", CARD_BG, "no")], icon="⚠️")
        if dlg.result == "yes":
            self._save_current_progress()
            self._save_weekly_plan()
            self._show_today_view()
        elif self.timer_running and not was_paused:
            self._start_mono  = time.monotonic()
            self.timer_paused = False
            self.pause_btn.configure(text="⏸  일시정지", bg=WARNING)
            self._render_loop()

    def _all_done(self):
        self._stop_loops()
        self.timer_running = False
        self._save_weekly_plan()
        self._show_all_done_window()

    def _show_all_done_window(self):
        win = tk.Toplevel(self)
        win.title("🎉 공부 완료!")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        w, h = 560, 380
        self.update_idletasks()
        px = self.winfo_rootx() + self.winfo_width()//2 - w//2
        py = self.winfo_rooty() + self.winfo_height()//2 - h//2
        win.geometry(f"{w}x{h}+{px}+{py}")

        outer = tk.Frame(win, bg=BG)
        outer.pack(fill="both", expand=True, padx=2, pady=2)
        card = tk.Frame(outer, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Frame(card, bg=SUCCESS, width=6).pack(side="left", fill="y")
        body = tk.Frame(card, bg=CARD_BG)
        body.pack(side="left", fill="both", expand=True, padx=24, pady=24)

        for text, font, fg in [
            ("🎉", ("Segoe UI Emoji", 56), SUCCESS),
            ("축하합니다!", ("Georgia", 22, "bold"), SUCCESS),
            ("오늘의 공부량을 끝내셨습니다.", ("Malgun Gothic", 13), TEXT),
            ("📚  수고하셨어요! 푹 쉬세요  ☕", ("Malgun Gothic", 10), TEXT_DIM),
        ]:
            tk.Label(body, text=text, font=font, bg=CARD_BG, fg=fg).pack(pady=(10 if text=="🎉" else 4, 4))

        def go_main(): win.destroy(); self._reset_all()
        tk.Button(body, text="🏠  메인화면으로 돌아가기",
                  font=("Malgun Gothic", 12, "bold"), bg=LIGHT_RED, fg="#000000",
                  activebackground=LIGHT_RED_HOVER, relief="flat", cursor="hand2",
                  padx=28, pady=12, bd=0, command=go_main).pack(pady=(8, 4))
        win.protocol("WM_DELETE_WINDOW", go_main)

    def _reset_all(self):
        self._stop_loops()
        self.timer_running = self.timer_paused = False
        self.anim_progress = self._elapsed_at_pause = 0.0
        self.timer_view.pack_forget()
        self.tab_header.pack(fill="x")
        self._switch_tab("today")
        self.pause_btn.configure(text="⏸  일시정지", bg=WARNING, state="normal")
        for lbl, val, fg in [(self.lbl_subject_name, "", ACCENT),
                             (self.lbl_subject_index, "", TEXT),
                             (self.lbl_timer, "00:00", TEXT),
                             (self.lbl_char_prop, "", TEXT)]:
            lbl.configure(text=val, fg=fg)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 미니 시간표
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _refresh_mini_schedule(self, current_idx, color):
        for w in self.mini_schedule.winfo_children(): w.destroy()
        tk.Label(self.mini_schedule, text="시간표", font=("Malgun Gothic", 10),
                 bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(0, 6))
        row = tk.Frame(self.mini_schedule, bg=BG)
        row.pack(fill="x")
        for i, subj in enumerate(self.subjects):
            if i < current_idx:   sc, st, ab = TEXT_DIM, "✓", CARD_BG
            elif i == current_idx: sc, st, ab = subj["color"], "▶", CARD_BG
            else:                  sc, st, ab = BORDER, "○", BG
            c_icon, _ = CHARACTERS.get(subj.get("character", "turtle"), ("", ""))
            p_icon, _ = PROPS.get(subj.get("prop", "box"), ("", ""))
            pill = tk.Frame(row, bg=ab, highlightthickness=1,
                            highlightbackground=sc if i == current_idx else BORDER)
            pill.pack(side="left", padx=4, pady=2)
            tk.Label(pill, text=f"{st} {subj['name']} ({subj['minutes']}분)  {c_icon}{p_icon}",
                     font=("Malgun Gothic", 9), bg=ab, fg=sc, padx=8, pady=4).pack()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 애니메이션 배경
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _on_canvas_resize(self, event):
        self._rebuild_track(); self._draw_scene(self.anim_progress)

    def _rebuild_track(self):
        c = self.anim_canvas
        w, h = c.winfo_width() or 800, c.winfo_height() or 140
        gy = h - 22
        self.anim_w, self.anim_h, self.anim_ground = w, h, gy
        self.anim_start_x, self.anim_end_x = 50, w - 50
        c.delete("all")
        color = self.anim_color

        # 그라데이션 배경
        for i in range(0, h-30, 4):
            t = i / (h-30)
            shade = _rgb_hex(0x1c + t*(0x0f-0x1c), 0x23 + t*(0x11-0x23), 0x33 + t*(0x17-0x33))
            c.create_line(0, i, w, i, fill=shade, tags="bg")

        # 땅
        c.create_rectangle(0, gy, w, h, fill="#1a2e1a", outline="", tags="bg")
        c.create_rectangle(0, gy, w, gy+4, fill="#2d5a1b", outline="", tags="bg")
        for x in range(self.anim_start_x+20, self.anim_end_x-20, 28):
            c.create_line(x, gy-1, x+14, gy-1, fill="#2d3f2d", width=2, tags="bg")

        # 시작/끝 표지
        sx = self.anim_start_x
        c.create_rectangle(sx-18, gy-32, sx+18, gy-10, fill="#2d3748", outline=TEXT_DIM, width=1, tags="bg")
        c.create_text(sx, gy-21, text="START", fill=TEXT_DIM, font=("Courier New", 7, "bold"), tags="bg")
        ex = self.anim_end_x
        c.create_line(ex, gy-50, ex, gy, fill=color, width=2, tags="bg")
        c.create_polygon(ex, gy-50, ex+22, gy-41, ex, gy-32, fill=color, outline="", tags="bg")
        c.create_text(ex, gy+10, text="END", fill=color, font=("Courier New", 7, "bold"), tags="bg")

        # 구름
        for cx_c, cy_c, r_c in [(w*0.25, 18, 14), (w*0.6, 12, 10), (w*0.8, 20, 12)]:
            c.create_oval(cx_c-r_c, cy_c-r_c*0.6, cx_c+r_c, cy_c+r_c*0.6, fill="#2a3a4a", outline="", tags="bg")
            c.create_oval(cx_c-r_c*0.5, cy_c-r_c, cx_c+r_c*0.5, cy_c+r_c*0.2, fill="#2a3a4a", outline="", tags="bg")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 씬 그리기
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def _draw_scene(self, progress):
        c, gy, t = self.anim_canvas, self.anim_ground, time.time()
        travel = self.anim_end_x - self.anim_start_x
        char_x = self.anim_start_x + travel * progress
        c.delete("dyn")
        color  = self.anim_color

        # 그림자
        c.create_oval(char_x-18, gy-4, char_x+18, gy+4, fill="#0a1010", outline="", tags="dyn")

        px = min(char_x + 28, self.anim_end_x + 8)
        if self.prop.get() == "box": self._draw_box(c, px, gy, progress, t, color)
        else:                         self._draw_ball(c, px, gy, progress, t, color)

        draw_fn = {"turtle": self._draw_turtle, "rabbit": self._draw_rabbit,
                   "dinosaur": self._draw_dinosaur, "dog": self._draw_dog,
                   "cat": self._draw_cat}.get(self.character.get(), self._draw_turtle)
        draw_fn(c, char_x, gy, t, color)

    def _anim_vars(self, t, walk_speed, bob_speed, bob_amp, extra_speed=None):
        if self.timer_paused:
            return (0.0, 0.0) if extra_speed is None else (0.0, 0.0, 0.0)
        walk = t * walk_speed
        bob  = math.sin(t * bob_speed) * bob_amp
        if extra_speed is None: return walk, bob
        return walk, bob, math.sin(t * extra_speed) * (6 if extra_speed > 5 else 8)

    # ── 박스 ──
    def _draw_box(self, c, px, gy, progress, t, color):
        wobble = 0.0 if self.timer_paused else math.sin(t*12) * 1.5
        tilt   = 0   if self.timer_paused else int(math.sin(t*8) * 2)
        bx, by = px, gy - 28 + wobble
        c.create_polygon(bx+14, by, bx+20, by-6, bx+20, by+16, bx+14, by+22,
                         fill=color_darken(color, 0.55), outline="", tags="dyn")
        c.create_polygon(bx-14, by, bx+14, by, bx+20, by-6, bx-8, by-6,
                         fill=color_lighten(color, 0.3), outline="", tags="dyn")
        c.create_rectangle(bx-14+tilt, by, bx+14+tilt, by+22,
                           fill=color, outline=color_darken(color, 0.4), width=1, tags="dyn")
        mid_y = by + 11
        c.create_line(bx-14+tilt, mid_y, bx+14+tilt, mid_y,
                      fill=color_darken(color, 0.35), width=1, tags="dyn")
        c.create_line(bx+tilt, by, bx+tilt, by+22,
                      fill=color_darken(color, 0.35), width=1, tags="dyn")
        c.create_oval(bx-10, gy-3, bx+18, gy+3, fill="#0a1010", outline="", tags="dyn")

    # ── 공 ──
    def _draw_ball(self, c, px, gy, progress, t, color):
        r = 14
        bounce = 0.0 if self.timer_paused else abs(math.sin(t*8)) * 5
        angle  = 0.0 if self.timer_paused else t * 5.0
        cy_ball = gy - r - bounce
        c.create_oval(px-r*0.9, gy-4, px+r*0.9, gy+3, fill="#0a1010", outline="", tags="dyn")
        c.create_oval(px-r, cy_ball-r, px+r, cy_ball+r,
                      fill=color, outline=color_darken(color, 0.35), width=2, tags="dyn")
        c.create_oval(px-r*0.5, cy_ball-r*0.7, px-r*0.05, cy_ball-r*0.25,
                      fill=color_lighten(color, 0.45), outline="", tags="dyn")
        for offset in [0, math.pi]:
            a = angle + offset
            cx_line = px + math.sin(a) * r * 0.7
            c.create_arc(cx_line-r*0.3, cy_ball-r, cx_line+r*0.3, cy_ball+r,
                         start=0, extent=180 if math.cos(a) >= 0 else -180,
                         style="arc", outline=color_darken(color, 0.3), width=1, tags="dyn")

    # ── 거북이 ──
    def _draw_turtle(self, c, cx, gy, t, color):
        walk, bob = self._anim_vars(t, 3.5, 7, 1.8)
        cy = gy - 24 + bob
        c.create_oval(cx-26, cy-3, cx-14, cy+7, fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")
        for lx, phase in [(-14, 0), (-6, math.pi)]:
            swing = math.sin(walk+phase) * 6
            lby = cy + 12 + swing
            c.create_oval(cx+lx-7, lby-5, cx+lx+7, lby+5, fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")
            c.create_oval(cx+lx-5, lby+1, cx+lx+5, lby+8, fill="#2e6b4f", outline="#1b4332", width=1, tags="dyn")
        c.create_oval(cx-22, cy-16, cx+22, cy+14, fill="#2d6a4f", outline="#1b4332", width=2, tags="dyn")
        c.create_oval(cx-18, cy-20, cx+18, cy+6, fill=color, outline=color_darken(color, 0.4), width=2, tags="dyn")
        sc = color_darken(color, 0.25)
        for rx1, ry1, rx2, ry2 in [(-8, -17, 8, -4), (-14, -9, -3, 2), (3, -9, 14, 2)]:
            c.create_oval(cx+rx1, cy+ry1, cx+rx2, cy+ry2,
                          fill=color_darken(color, 0.15), outline=sc, width=1, tags="dyn")
        for lx, phase in [(8, math.pi), (16, 0)]:
            swing = math.sin(walk+phase) * 6
            lby = cy + 10 + swing
            c.create_oval(cx+lx-6, lby-5, cx+lx+6, lby+5, fill="#3d8b65", outline="#1b4332", width=1, tags="dyn")
            c.create_oval(cx+lx-5, lby+1, cx+lx+5, lby+8, fill="#2e6b4f", outline="#1b4332", width=1, tags="dyn")
        c.create_oval(cx+16, cy-8, cx+28, cy+4, fill="#40916c", outline="#1b4332", width=1, tags="dyn")
        hx, hy = cx+30, cy-12
        c.create_oval(hx-13, hy-10, hx+13, hy+14, fill="#40916c", outline="#1b4332", width=2, tags="dyn")
        ex, ey = hx+3, hy-2
        c.create_oval(ex-5, ey-5, ex+5, ey+5, fill="white", outline="#1b4332", width=1, tags="dyn")
        c.create_oval(ex-2, ey-2, ex+3, ey+3, fill="#1a1a2e", tags="dyn")
        c.create_oval(ex-1, ey-4, ex+1, ey-2, fill="white", tags="dyn")
        c.create_arc(hx-5, hy+2, hx+7, hy+12, start=200, extent=-160, style="arc",
                     outline="#1b4332", width=2, tags="dyn")
        c.create_oval(hx+5, hy+2, hx+9, hy+5, fill="#2e6b4f", outline="", tags="dyn")

    # ── 토끼 ──
    def _draw_rabbit(self, c, cx, gy, t, color):
        walk, bob = self._anim_vars(t, 5.0, 10, 2.5)
        ear_sway = 0.0 if self.timer_paused else math.sin(t*4) * 3
        cy = gy - 28 + bob
        c.create_oval(cx-26, cy+2, cx-12, cy+16, fill="white", outline="#d0c8cc", width=1, tags="dyn")
        c.create_oval(cx-24, cy+4, cx-15, cy+14, fill="#f0eaec", outline="", tags="dyn")
        for lx, phase in [(-12, 0), (0, math.pi)]:
            swing = math.sin(walk+phase) * 7
            lby = cy + 14 + swing
            c.create_oval(cx+lx-10, lby-4, cx+lx+10, lby+6, fill="#f0e6eb", outline="#c9b2c5", width=1, tags="dyn")
            for toe in [-4, 0, 4]:
                c.create_oval(cx+lx+toe-2, lby+3, cx+lx+toe+2, lby+7, fill="#e8d8e0", outline="", tags="dyn")
        c.create_oval(cx-20, cy-14, cx+20, cy+18, fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        c.create_oval(cx-10, cy-4, cx+12, cy+14, fill="#faf4f7", outline="", tags="dyn")
        for lx, phase in [(10, math.pi), (18, 0)]:
            swing = math.sin(walk+phase) * 5
            lby = cy + 10 + swing
            c.create_oval(cx+lx-7, lby-4, cx+lx+7, lby+5, fill="#f0e6eb", outline="#c9b2c5", width=1, tags="dyn")
        hx, hy = cx+20, cy-20
        c.create_oval(hx-15, hy-12, hx+15, hy+15, fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        c.create_oval(hx+5, hy+3, hx+13, hy+11, fill="#f4c2cc", outline="", tags="dyn")
        edx = ear_sway * 0.5
        c.create_oval(hx+(-2+edx), hy-42, hx+(8+edx), hy-12,
                      fill="#f0e8ed", outline="#c9b2c5", width=1, tags="dyn")
        c.create_oval(hx+edx, hy-40+edx*0.3, hx+6+edx, hy-14,
                      fill=color_lighten(color, 0.2), outline="", tags="dyn")
        c.create_oval(hx-12-ear_sway, hy-44, hx-2-ear_sway, hy-12,
                      fill="#f0e8ed", outline="#c9b2c5", width=2, tags="dyn")
        c.create_oval(hx-10-ear_sway, hy-42, hx-4-ear_sway, hy-14,
                      fill=color_lighten(color, 0.2), outline="", tags="dyn")
        ex, ey = hx+6, hy-4
        c.create_oval(ex-5, ey-5, ex+5, ey+5, fill="white", outline="#c9b2c5", width=1, tags="dyn")
        c.create_oval(ex-2, ey-2, ex+3, ey+3, fill="#2a1a2e", tags="dyn")
        c.create_oval(ex-1, ey-4, ex+1, ey-2, fill="white", tags="dyn")
        c.create_oval(hx+8, hy+3, hx+14, hy+8, fill="#f9a8c9", outline="", tags="dyn")
        for wy, wlen in [(hy+2, 12), (hy+5, 10), (hy+8, 11)]:
            c.create_line(hx+8, wy, hx+8+wlen, wy-1, fill="#d0bcc5", width=1, tags="dyn")
        c.create_arc(hx+5, hy+6, hx+14, hy+14, start=220, extent=-140,
                     style="arc", outline="#c9b2c5", width=1, tags="dyn")

    # ── 공룡 ──
    def _draw_dinosaur(self, c, cx, gy, t, color):
        walk, bob = self._anim_vars(t, 4.0, 8, 2.0)
        cy = gy - 30 + bob
        BC, BD, BL = "#5fa843", "#2e5e1f", "#a8d68c"
        c.create_polygon(cx-32, cy+6, cx-38, cy-2, cx-30, cy+2, cx-16, cy+8, cx-16, cy+14,
                         fill=BC, outline=BD, width=1, tags="dyn")
        for lx, phase in [(-8, 0), (2, math.pi)]:
            swing = math.sin(walk+phase) * 6
            lby = cy + 16 + swing
            c.create_oval(cx+lx-8, cy+4, cx+lx+8, cy+18, fill=BC, outline=BD, width=1, tags="dyn")
            c.create_oval(cx+lx-9, lby+2, cx+lx+11, lby+9, fill=BD, outline=BD, width=1, tags="dyn")
            for toe in [-6, 0, 6]:
                c.create_polygon(cx+lx+toe, lby+6, cx+lx+toe+2, lby+10, cx+lx+toe-2, lby+10,
                                 fill="#1a1a1a", outline="", tags="dyn")
        c.create_oval(cx-18, cy-12, cx+22, cy+18, fill=BC, outline=BD, width=2, tags="dyn")
        c.create_oval(cx-10, cy+0, cx+18, cy+16, fill=BL, outline="", tags="dyn")
        for ly in [cy+4, cy+9]:
            c.create_line(cx-6, ly, cx+14, ly, fill=color_darken(BL, 0.2), width=1, tags="dyn")
        spikes = [(cx-16,cy-8),(cx-12,cy-16),(cx-6,cy-12),(cx-2,cy-20),
                  (cx+4,cy-14),(cx+10,cy-22),(cx+16,cy-16),(cx+22,cy-22)]
        for i in range(0, len(spikes)-1, 2):
            p1, p2 = spikes[i], spikes[i+1]
            c.create_polygon(p1[0], p1[1], p2[0], p2[1], (p1[0]+p2[0])/2+4, p1[1]-2,
                             fill=color, outline=color_darken(color, 0.4), width=1, tags="dyn")
        for lx, phase in [(12, math.pi), (18, 0)]:
            swing = math.sin(walk+phase) * 3
            lby = cy + 6 + swing
            c.create_oval(cx+lx-4, lby-2, cx+lx+4, lby+7, fill=BC, outline=BD, width=1, tags="dyn")
        hx, hy = cx+26, cy-18
        c.create_polygon(cx+18, cy-8, cx+22, cy-14, hx+2, hy+6, hx-2, hy+12,
                         fill=BC, outline=BD, width=1, tags="dyn")
        c.create_oval(hx-12, hy-10, hx+18, hy+12, fill=BC, outline=BD, width=2, tags="dyn")
        c.create_arc(hx-6, hy+0, hx+18, hy+14, start=180, extent=180,
                     fill=color_darken(BC, 0.5), outline=BD, width=1, tags="dyn")
        for tx in [hx-2, hx+4, hx+10]:
            c.create_polygon(tx, hy+7, tx+3, hy+12, tx-3, hy+12, fill="white", outline="", tags="dyn")
        ex, ey = hx+6, hy-3
        c.create_oval(ex-5, ey-5, ex+5, ey+5, fill="white", outline=BD, width=1, tags="dyn")
        c.create_oval(ex-2, ey-2, ex+3, ey+3, fill="#1a1a1a", tags="dyn")
        c.create_oval(ex-1, ey-4, ex+1, ey-2, fill="white", tags="dyn")
        c.create_oval(hx+14, hy+2, hx+16, hy+4, fill=BD, outline="", tags="dyn")

    # ── 강아지 ──
    def _draw_dog(self, c, cx, gy, t, color):
        walk, bob = self._anim_vars(t, 5.0, 10, 2.0)
        tail_swing = 0.0 if self.timer_paused else math.sin(t*12) * 6
        cy = gy - 26 + bob
        BC, BD, BL, EC = "#d4a574", "#8b6342", "#f0d9b8", "#a67c52"
        tx_end, ty_end = cx-24+tail_swing, cy-14
        c.create_line(cx-16, cy-4, cx-22, cy-10, tx_end, ty_end,
                      fill=BC, width=6, capstyle="round", tags="dyn")
        c.create_oval(tx_end-4, ty_end-4, tx_end+4, ty_end+4, fill=BC, outline=BD, width=1, tags="dyn")
        for lx, phase in [(-10, 0), (-2, math.pi)]:
            swing = math.sin(walk+phase) * 5
            lby = cy + 14 + swing
            c.create_oval(cx+lx-5, cy+4, cx+lx+5, cy+18, fill=BC, outline=BD, width=1, tags="dyn")
            c.create_oval(cx+lx-6, lby+1, cx+lx+7, lby+7, fill=BD, outline=BD, width=1, tags="dyn")
        c.create_oval(cx-18, cy-8, cx+18, cy+16, fill=BC, outline=BD, width=2, tags="dyn")
        c.create_oval(cx-10, cy+2, cx+14, cy+14, fill=BL, outline="", tags="dyn")
        c.create_oval(cx-8, cy-4, cx-2, cy+1, fill=color, outline="", tags="dyn")
        c.create_oval(cx+2, cy-6, cx+10, cy+0, fill=color, outline="", tags="dyn")
        for lx, phase in [(8, math.pi), (14, 0)]:
            swing = math.sin(walk+phase) * 5
            lby = cy + 14 + swing
            c.create_oval(cx+lx-5, cy+4, cx+lx+5, cy+16, fill=BC, outline=BD, width=1, tags="dyn")
            c.create_oval(cx+lx-6, lby+1, cx+lx+6, lby+6, fill=BD, outline=BD, width=1, tags="dyn")
        hx, hy = cx+20, cy-14
        c.create_oval(hx-13, hy-11, hx+14, hy+14, fill=BC, outline=BD, width=2, tags="dyn")
        c.create_polygon(hx-6, hy-8, hx-14, hy+4, hx-4, hy+6, fill=EC, outline=BD, width=1, tags="dyn")
        c.create_polygon(hx+4, hy-10, hx-2, hy+4, hx+8, hy+4, fill=EC, outline=BD, width=1, tags="dyn")
        c.create_oval(hx+4, hy+4, hx+18, hy+16, fill=BL, outline=BD, width=1, tags="dyn")
        c.create_oval(hx+13, hy+6, hx+18, hy+10, fill="#1a1a1a", outline="", tags="dyn")
        c.create_arc(hx+6, hy+9, hx+16, hy+16, start=200, extent=-140, style="arc",
                     outline=BD, width=1, tags="dyn")
        c.create_oval(hx+9, hy+13, hx+13, hy+17, fill="#f48fb1", outline="", tags="dyn")
        ex, ey = hx+2, hy-2
        c.create_oval(ex-4, ey-4, ex+4, ey+4, fill="white", outline=BD, width=1, tags="dyn")
        c.create_oval(ex-2, ey-2, ex+2, ey+2, fill="#1a1a1a", tags="dyn")
        c.create_oval(ex-1, ey-3, ex+1, ey-1, fill="white", tags="dyn")

    # ── 고양이 ──
    def _draw_cat(self, c, cx, gy, t, color):
        walk, bob = self._anim_vars(t, 4.5, 9, 1.8)
        tail_sway = 0.0 if self.timer_paused else math.sin(t*3) * 8
        cy = gy - 26 + bob
        BC, BD, BL = "#9e9e9e", "#555555", "#e0e0e0"
        stripe = color_darken(BC, 0.3)
        tx_end, ty_end = cx-22, cy-28+tail_sway
        c.create_line(cx-16, cy+2, cx-20, cy-8, cx-22, cy-18, tx_end, ty_end,
                      fill=BC, width=6, capstyle="round", smooth=True, tags="dyn")
        c.create_oval(tx_end-4, ty_end-4, tx_end+4, ty_end+4, fill=stripe, outline=BD, width=1, tags="dyn")
        for lx, phase in [(-10, 0), (-2, math.pi)]:
            swing = math.sin(walk+phase) * 5
            lby = cy + 14 + swing
            c.create_oval(cx+lx-5, cy+4, cx+lx+5, cy+16, fill=BC, outline=BD, width=1, tags="dyn")
            c.create_oval(cx+lx-6, lby+1, cx+lx+6, lby+6, fill=BD, outline=BD, width=1, tags="dyn")
        c.create_oval(cx-18, cy-8, cx+18, cy+16, fill=BC, outline=BD, width=2, tags="dyn")
        c.create_oval(cx-10, cy+2, cx+14, cy+14, fill=BL, outline="", tags="dyn")
        for sx_ in [cx-8, cx-2, cx+4, cx+10]:
            c.create_line(sx_, cy-6, sx_, cy-2, fill=stripe, width=2, tags="dyn")
        for lx, phase in [(8, math.pi), (14, 0)]:
            swing = math.sin(walk+phase) * 4
            lby = cy + 14 + swing
            c.create_oval(cx+lx-5, cy+4, cx+lx+5, cy+16, fill=BC, outline=BD, width=1, tags="dyn")
            c.create_oval(cx+lx-6, lby+1, cx+lx+6, lby+6, fill=BD, outline=BD, width=1, tags="dyn")
        hx, hy = cx+20, cy-14
        c.create_oval(hx-12, hy-10, hx+14, hy+14, fill=BC, outline=BD, width=2, tags="dyn")
        c.create_polygon(hx-10, hy-6, hx-6, hy-20, hx-2, hy-8, fill=BC, outline=BD, width=1, tags="dyn")
        c.create_polygon(hx-8, hy-8, hx-6, hy-16, hx-4, hy-9, fill=color, outline="", tags="dyn")
        c.create_polygon(hx+2, hy-8, hx+6, hy-22, hx+12, hy-6, fill=BC, outline=BD, width=1, tags="dyn")
        c.create_polygon(hx+4, hy-9, hx+6, hy-18, hx+10, hy-8, fill=color, outline="", tags="dyn")
        c.create_line(hx-4, hy-8, hx-2, hy-4, fill=stripe, width=2, tags="dyn")
        c.create_line(hx+2, hy-8, hx+4, hy-4, fill=stripe, width=2, tags="dyn")
        c.create_oval(hx+0, hy+4, hx+14, hy+14, fill=BL, outline=BD, width=1, tags="dyn")
        c.create_polygon(hx+7, hy+5, hx+10, hy+5, hx+8, hy+8, fill="#f4a8b8", outline=BD, width=1, tags="dyn")
        c.create_line(hx+8, hy+8, hx+8, hy+11, fill=BD, width=1, tags="dyn")
        c.create_arc(hx+4, hy+9, hx+9, hy+13, start=0, extent=-180, style="arc", outline=BD, width=1, tags="dyn")
        c.create_arc(hx+8, hy+9, hx+13, hy+13, start=0, extent=-180, style="arc", outline=BD, width=1, tags="dyn")
        for wy, wlen in [(hy+7, 10), (hy+10, 9)]:
            c.create_line(hx+12, wy, hx+12+wlen, wy-1, fill="#cccccc", width=1, tags="dyn")
            c.create_line(hx+2, wy, hx+2-wlen, wy-1, fill="#cccccc", width=1, tags="dyn")
        ex, ey = hx+4, hy-2
        c.create_oval(ex-4, ey-4, ex+4, ey+4, fill="#c5e890", outline=BD, width=1, tags="dyn")
        c.create_oval(ex-1, ey-3, ex+1, ey+3, fill="#1a1a1a", tags="dyn")

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
        tk.Radiobutton(frame, text=f"  {icon}  {label}", variable=variable, value=value,
                       font=("Malgun Gothic", 11), bg=SIDEBAR_BG, fg=TEXT,
                       activebackground=SIDEBAR_BG, selectcolor=CARD_BG,
                       indicatoron=True, relief="flat", cursor="hand2").pack(anchor="w")

    def _entry(self, parent):
        return tk.Entry(parent, font=("Malgun Gothic", 11), bg=CARD_BG, fg=TEXT,
                        insertbackground=TEXT, relief="flat", bd=6,
                        highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)


if __name__ == "__main__":
    app = StudyTimerApp()
    app.mainloop()
