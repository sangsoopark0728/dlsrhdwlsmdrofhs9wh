import pygame
import math
import random
import time

# ===== 초기화 및 설정 =====
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

WIDTH, HEIGHT = 500, 720  # 공룡이 지나갈 공간을 위해 가로폭을 넓힘
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎵 Rhythm Dino - Step by Step")
clock = pygame.time.Clock()

# ===== 폰트 설정 =====
try:
    FONT_ORBITRON = pygame.font.SysFont("Arial", 20, bold=True)
    FONT_JUDGE = pygame.font.SysFont("Arial", 45, bold=True)
    FONT_COMBO = pygame.font.SysFont("Arial", 28, bold=True)
    FONT_RANK = pygame.font.SysFont("Arial", 90, bold=True)
except:
    FONT_ORBITRON = pygame.font.Font(None, 24)
    FONT_JUDGE = pygame.font.Font(None, 50)
    FONT_COMBO = pygame.font.Font(None, 32)
    FONT_RANK = pygame.font.Font(None, 100)

# ===== 게임 상수 =====
JUDGE_Y = 630
NOTE_SPEED = 420
APPROACH_TIME = JUDGE_Y / NOTE_SPEED

# ===== 오디오 주파수 합성 =====
NOTE_FREQ = {
    'C3':130.81,'D3':146.83,'E3':164.81,'F3':174.61,'G3':196.00,'A3':220.00,'B3':246.94,
    'C4':261.63,'C#4':277.18,'D4':293.66,'D#4':311.13,'E4':329.63,'F4':349.23,
    'F#4':369.99,'G4':392.00,'G#4':415.30,'A4':440.00,'A#4':466.16,'B4':493.88,
    'C5':523.25,'C#5':554.37,'D5':587.33,'D#5':622.25,'E5':659.25,'F5':698.46,
    'F#5':739.99,'G5':783.99,'G#5':830.61,'A5':880.00,'A#5':932.33,'B5':987.77,
    'C6':1046.50,'D6':1174.66,'E6':1318.51
}

def generate_tone_sound(frequency, duration_sec, volume=0.15):
    sample_rate = 44100
    num_samples = int(sample_rate * duration_sec)
    buf = bytearray()
    for i in range(num_samples):
        t = i / sample_rate
        value = int(32767 * volume * math.sin(2 * math.pi * frequency * t))
        if num_samples - i < int(sample_rate * 0.05): 
            factor = (num_samples - i) / (sample_rate * 0.05)
            value = int(value * factor)
        try:
            packed = value.to_bytes(2, byteorder='little', signed=True)
            buf.extend(packed) 
            buf.extend(packed) 
        except:
            buf.extend(b'\x00\x00\x00\x00')
    return pygame.mixer.Sound(buffer=buf)

# ===== 음악 데이터 =====
furElise = [
    ['E5',0.25],['D#5',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['B4',0.25],['D5',0.25],['C5',0.25],
    ['A4',0.5],['C4',0.25],['E4',0.25],['A4',0.25],['B4',0.5],['E4',0.25],['G#4',0.25],['B4',0.25],
    ['C5',0.5],['E4',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['B4',0.25],
    ['D5',0.25],['C5',0.25],['A4',0.5],['C4',0.25],['E4',0.25],['A4',0.25],['B4',0.5],['E4',0.25],
    ['C5',0.25],['B4',0.25],['A4',0.75],['B4',0.25],['C5',0.25],['D5',0.5],['G3',0.25],['F5',0.25],
    ['E5',0.5],['C3',0.25],['E5',0.25],['D5',0.25],['C5',0.25],['B4',0.5],['E4',0.25],['B4',0.25],
    ['C5',0.25],['D5',0.5],['G3',0.25],['G5',0.25],['F5',0.25],['E5',0.5],['C3',0.25],['E5',0.25],
    ['D5',0.25],['C5',0.25],['B4',0.5],['E4',0.25],['C5',0.25],['B4',0.25],['A4',0.75]
]

nachtmusik = [
    ['G4',0.25],['D5',0.25],['G4',0.25],['D5',0.25],['G4',0.25],['D5',0.25],['G5',0.5],['A5',0.25],
    ['G5',0.25],['F#5',0.25],['G5',0.25],['A5',0.5],['D4',0.25],['A4',0.25],['D4',0.25],['A4',0.25],
    ['D4',0.25],['A4',0.25],['D5',0.5],['E5',0.25],['D5',0.25],['C#5',0.25],['D5',0.25],['E5',0.5]
]

songs = [
    { "name": "Für Elise", "composer": "Beethoven", "melody": furElise, "tempo": 0.32, "color": (80, 80, 80) },
    { "name": "Eine kleine Nachtmusik", "composer": "Mozart", "melody": nachtmusik, "tempo": 0.28, "color": (80, 80, 80) }
]

# ===== 게임 변수 상태 그룹 =====
game_state = "MENU" 
selected_song_idx = 0

notes = []
perfect, good, bad, miss, combo, maxCombo, score = 0, 0, 0, 0, 0, 0, 0
start_time = 0
song_duration = 0
current_song = None

is_any_key_pressed = False

judge_text = ""
judge_color = (255, 255, 255)
judge_time = 0
audio_queue = []

# ===== 🦖 공룡 관련 변수 =====
dino_x = 50
dino_target_x = 50
dino_y = 170  # 미니 게임 화면의 바닥 높이
dino_jump_y = 0
dino_jump_speed = 0
dino_is_walking = False

def generate_notes(song_data):
    global song_duration
    generated = []
    t = APPROACH_TIME
    audio_schedule = []

    for note, beat in song_data["melody"]:
        dur = beat * song_data["tempo"] * 4
        freq = NOTE_FREQ.get(note, 440)
        
        if freq:
            audio_schedule.append({
                "play_time": t,
                "sound": generate_tone_sound(freq, dur * 0.9)
            })

        # ❗ [수정] 롱노트 속성을 제거하고 전부 일반 단노트로 생성합니다.
        generated.append({
            "lane": 0,
            "time": t,
            "hit": False,
            "done": False,
        })
        t += dur
        
    song_duration = t + 1
    return generated, audio_schedule

def start_game(idx):
    global notes, audio_queue, perfect, good, bad, miss, combo, maxCombo, score
    global is_any_key_pressed, start_time, game_state, current_song, judge_text
    global dino_x, dino_target_x, dino_jump_y, dino_jump_speed
    
    perfect = good = bad = miss = combo = maxCombo = score = 0
    is_any_key_pressed = False
    judge_text = ""
    
    # 공룡 위치 초기화
    dino_x = 50
    dino_target_x = 50
    dino_jump_y = 0
    dino_jump_speed = 0
    
    current_song = songs[idx]
    notes, audio_queue = generate_notes(current_song)
    
    start_time = time.time()
    game_state = "PLAYING"

def trigger_judge(text, color):
    global judge_text, judge_color, judge_time
    judge_text = text
    judge_color = color
    judge_time = time.time()

# ===== 🦖 공룡 그리기 함수 (도트 그래픽 스타일) =====
def draw_dino(surface, x, y):
    # 공룡 몸통 및 머리
    pygame.draw.rect(surface, (80, 80, 80), (x, y - 40, 24, 26))      # 몸통
    pygame.draw.rect(surface, (80, 80, 80), (x + 12, y - 56, 22, 18)) # 머리
    pygame.draw.rect(surface, (80, 80, 80), (x - 6, y - 34, 8, 12))   # 꼬리
    # 눈
    pygame.draw.rect(surface, (240, 240, 240), (x + 18, y - 52, 4, 4))
    # 발 (걷는 애니메이션용 시각화)
    step = int(time.time() * 10) % 2
    if step == 0:
        pygame.draw.rect(surface, (80, 80, 80), (x + 4, y - 14, 4, 14))
        pygame.draw.rect(surface, (80, 80, 80), (x + 14, y - 14, 4, 8))
    else:
        pygame.draw.rect(surface, (80, 80, 80), (x + 4, y - 14, 4, 8))
        pygame.draw.rect(surface, (80, 80, 80), (x + 14, y - 14, 4, 14))

# ===== 메인 루프 =====
running = True
while running:
    current_time_sec = time.time() - start_time if game_state == "PLAYING" else 0
    
    # 1. 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if game_state == "MENU":
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    selected_song_idx = (selected_song_idx - 1) % len(songs)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    selected_song_idx = (selected_song_idx + 1) % len(songs)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    start_game(selected_song_idx)
                    
            elif game_state == "RESULT":
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    game_state = "MENU"

    # 실시간 입력 확인 (인게임)
    if game_state == "PLAYING":
        pygame_keys = pygame.key.get_pressed()
        currently_pressed = any(pygame_keys[k] for k in [pygame.K_SPACE, pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k])
        
        if currently_pressed and not is_any_key_pressed:
            is_any_key_pressed = True
            
            closest = None
            closest_dist = float('inf')
            for n in notes:
                if not n["hit"] and not n["done"]:
                    dist = abs(current_time_sec - n["time"])
                    if dist < closest_dist:
                        closest_dist = dist
                        closest = n
                        
            if closest and closest_dist < 0.28:
                closest["hit"] = True
                closest["done"] = True
                
                # 🦖 [핵심 추가] 노트를 맞추면 공룡이 앞으로 전진하고 살짝 점프!
                dino_target_x += 18
                if dino_jump_y == 0:  # 바닥에 있을 때만 점프 트리거
                    dino_jump_speed = -10
                    
                if closest_dist < 0.07:
                    perfect += 1; score += 300; combo += 1
                    trigger_judge('PERFECT', (50, 180, 50))
                elif closest_dist < 0.16:
                    good += 1; score += 100; combo += 1
                    trigger_judge('GOOD', (180, 180, 50))
                else:
                    bad += 1; score += 50; combo = 0
                    trigger_judge('BAD', (180, 50, 50))
                if combo > maxCombo: maxCombo = combo

        elif not currently_pressed and is_any_key_pressed:
            is_any_key_pressed = False

    # 2. 게임 상태 업데이트 & 애니메이션 처리
    if game_state == "PLAYING":
        # 오디오 재생
        for audio in audio_queue:
            if not audio.get("played", False) and current_time_sec >= audio["play_time"]:
                audio["sound"].play()
                audio["played"] = True
                
        # 노트 미스 판정
        for n in notes:
            if n["done"]: continue
            head_y = (current_time_sec - (n["time"] - APPROACH_TIME)) * NOTE_SPEED
            if head_y > JUDGE_Y + 20 and not n["hit"]:
                n["done"] = True
                miss += 1; combo = 0
                trigger_judge('MISS', (200, 50, 50))

        # 🦖 공룡 이동 및 점프 물리 업데이트
        if dino_x < dino_target_x:
            dino_x += 2  # 부드럽게 목표 지점으로 전진
            
        # 공룡이 화면 밖으로 너무 멀리 가지 않도록 화면이 스크롤되는 연출 효과 (루프)
        if dino_x > WIDTH - 100:
            dino_x = 50
            dino_target_x = 50

        # 점프 처리
        if dino_jump_y < 0 or dino_jump_speed != 0:
            dino_jump_y += dino_jump_speed
            dino_speed_gravity = 0.8
            dino_jump_speed += dino_speed_gravity
            if dino_jump_y >= 0:
                dino_jump_y = 0
                dino_jump_speed = 0

        if current_time_sec > song_duration + 2:
            game_state = "RESULT"

    # 3. 그래픽 렌더링
    screen.fill((247, 247, 247)) # 오리지널 구글 디노 느낌의 깔끔한 백색 바탕
    
    if game_state == "MENU":
        screen.fill((10, 10, 26)) # 메뉴는 SF 스타일 유지
        title_surf = FONT_ORBITRON.render("🎹 SELECT DINO MUSIC", True, (255, 215, 0))
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 100))
        
        for idx, song in enumerate(songs):
            bg_color = (20, 30, 50) if idx == selected_song_idx else (13, 24, 42)
            border_color = (68, 102, 255) if idx == selected_song_idx else (34, 34, 51)
            rect_box = pygame.Rect(50, 200 + idx*110, 400, 90)
            pygame.draw.rect(screen, bg_color, rect_box, border_radius=10)
            pygame.draw.rect(screen, border_color, rect_box, width=2, border_radius=10)
            
            name_surf = FONT_ORBITRON.render(song["name"], True, (255, 255, 255))
            sub_surf = FONT_ORBITRON.render(song["composer"], True, (150, 150, 150))
            screen.blit(name_surf, (80, 220 + idx*110))
            screen.blit(sub_surf, (80, 250 + idx*110))
            
        guide_surf = FONT_ORBITRON.render("PRESS SPACE TO PLAY", True, (100, 100, 120))
        screen.blit(guide_surf, (WIDTH//2 - guide_surf.get_width()//2, 550))

    elif game_state == "PLAYING":
        # --- 🦖 상단: 공룡 월드 영역 ---
        # 지평선 (바닥 선)
        pygame.draw.line(screen, (80, 80, 80), (0, dino_y), (WIDTH, dino_y), 2)
        
        # 바닥 도트 장식 효과 (참고 이미지 스타일)
        for fx in [30, 120, 240, 310, 450]:
            pygame.draw.line(screen, (150, 150, 150), (fx, dino_y + 6), (fx + 4, dino_y + 6), 1)
            pygame.draw.line(screen, (150, 150, 150), (fx + 10, dino_y + 12), (fx + 15, dino_y + 12), 1)

        # 미니 선인장 장애물 렌더링
        pygame.draw.rect(screen, (120, 120, 120), (WIDTH - 80, dino_y - 25, 10, 25))
        pygame.draw.rect(screen, (120, 120, 120), (WIDTH - 85, dino_y - 20, 5, 8))
        pygame.draw.rect(screen, (120, 120, 120), (WIDTH - 72, dino_y - 16, 5, 8))

        # 공룡 그리기 (점프 높이 반영)
        draw_dino(screen, dino_x, dino_y + dino_jump_y)

        # 구역 나누는 분할선
        pygame.draw.line(screen, (200, 200, 200), (0, 240), (WIDTH, 240), 2)

        # --- 🎼 하단: 리듬 게임 영역 ---
        # 노트 레인 백그라운드
        pygame.draw.rect(screen, (235, 235, 235), (170, 240, 160, HEIGHT - 240))
        pygame.draw.line(screen, (210, 210, 210), (170, 240), (170, HEIGHT), 2)
        pygame.draw.line(screen, (210, 210, 210), (330, 240), (330, HEIGHT), 2)

        # 빨간색 판정선
        pygame.draw.line(screen, (255, 90, 90), (170, JUDGE_Y), (330, JUDGE_Y), 3)
        
        # 단노트만 떨어지도록 렌더링 (롱노트 코드 완전 삭제)
        for n in notes:
            if n["done"]: continue
            head_y = (current_time_sec - (n["time"] - APPROACH_TIME)) * NOTE_SPEED
            if head_y < 240 or head_y > HEIGHT: continue
            
            # 구글 감성의 다크 그레이 단노트 스타일
            pygame.draw.rect(screen, (80, 80, 80), (180, head_y, 140, 20), border_radius=4)

        # 하단 인터페이스 바
        pygame.draw.rect(screen, (220, 220, 220), (0, 640, WIDTH, 80))
        lbl = FONT_ORBITRON.render("ANY KEY = STEP!", True, (50, 50, 50))
        screen.blit(lbl, (WIDTH//2 - lbl.get_width()//2, 670))

        # 인포 메타 데이터
        score_surf = FONT_ORBITRON.render(f"SCORE: {score}", True, (50, 50, 50))
        screen.blit(score_surf, (20, 260))

        # 판정 연출
        if judge_text and (time.time() - judge_time < 0.4):
            j_surf = FONT_JUDGE.render(judge_text, True, judge_color)
            screen.blit(j_surf, (WIDTH//2 - j_surf.get_width()//2, 350))
            if combo > 1 and judge_text not in ['MISS', 'BAD']:
                c_surf = FONT_COMBO.render(f"{combo} COMBO", True, (80, 80, 250))
                screen.blit(c_surf, (WIDTH//2 - c_surf.get_width()//2, 410))

    elif game_state == "RESULT":
        screen.fill((10, 10, 26))
        total_notes = perfect + good + bad + miss
        accuracy = (perfect * 100 + good * 60 + bad * 20) / (total_notes * 100) * 100 if total_notes > 0 else 0
        
        res_title = FONT_ORBITRON.render("★ DINO RESULT ★", True, (255, 255, 255))
        screen.blit(res_title, (WIDTH//2 - res_title.get_width()//2, 80))
        
        details = [
            f"PERFECT : {perfect}",
            f"GOOD : {good}",
            f"MISS : {miss}",
            f"TOTAL SCORE : {score}",
            f"ACCURACY : {accuracy:.1f}%"
        ]
        for i, text in enumerate(details):
            det_surf = FONT_ORBITRON.render(text, True, (200, 200, 220))
            screen.blit(det_surf, (WIDTH//2 - det_surf.get_width()//2, 220 + i * 40))
            
        retry_surf = FONT_ORBITRON.render("PRESS SPACEBAR TO MENU", True, (255, 215, 0))
        screen.blit(retry_surf, (WIDTH//2 - retry_surf.get_width()//2, HEIGHT - 120))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
