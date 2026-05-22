import pygame
import math
import time

# ===== 초기화 및 설정 =====
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

WIDTH, HEIGHT = 640, 400  
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🦖 Rhythm Dino - Under the High Bar")
clock = pygame.time.Clock()

# ===== 폰트 설정 =====
try:
    FONT_ORBITRON = pygame.font.SysFont("Arial", 18, bold=True)
    FONT_JUDGE = pygame.font.SysFont("Arial", 40, bold=True)
    FONT_COMBO = pygame.font.SysFont("Arial", 24, bold=True)
except:
    FONT_ORBITRON = pygame.font.Font(None, 22)
    FONT_JUDGE = pygame.font.Font(None, 45)
    FONT_COMBO = pygame.font.Font(None, 28)

# ===== 게임 상수 =====
DINO_X = 140        # 공룡의 X 위치 (판정선 기준)
GROUND_Y = 280      # 바닥 높이
HURDLE_SPEED = 380  # 장애물 이동 속도 (픽셀/초)

# ===== 오디오 주파수 합성 =====
NOTE_FREQ = {
    'G3':196.00, 'A3':220.00, 'B3':246.94,
    'C4':261.63, 'D4':293.66, 'E4':329.63, 'F4':349.23, 'G4':392.00, 'A4':440.00, 'B4':493.88, 
    'C5':523.25, 'D5':587.33, 'E5':659.25, 'F5':698.46, 'G5':783.99, 'A5':880.00
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

# ===== 🎼 엘리제를 위하여 완벽 메인 테마 풀 버전 =====
furElise_Full = [
    ['E5',0.25], ['D5',0.25], ['E5',0.25], ['D5',0.25], ['E5',0.25], ['B4',0.25], ['D5',0.25], ['C5',0.25], ['A4',0.5],
    ['C4',0.25], ['E4',0.25], ['A4',0.25], ['B4',0.5],  ['E4',0.25], ['G4',0.25], ['B4',0.25], ['C5',0.5], ['E4',0.25],
    ['E5',0.25], ['D5',0.25], ['E5',0.25], ['D5',0.25], ['E5',0.25], ['B4',0.25], ['D5',0.25], ['C5',0.25], ['A4',0.5],
    ['C4',0.25], ['E4',0.25], ['A4',0.25], ['B4',0.5],  ['E4',0.25], ['C5',0.25], ['B4',0.25], ['A4',0.5],
    ['B4',0.25], ['C5',0.25], ['D5',0.5],  ['G4',0.25], ['F5',0.25], ['E5',0.5],  ['C4',0.25], ['E5',0.25], ['D5',0.5],
    ['B4',0.25], ['D5',0.25], ['C5',0.5],  ['E4',0.25], ['E5',0.25], ['D5',0.25], ['E5',0.25], ['D5',0.25], ['E5',0.25],
    ['B4',0.25], ['D5',0.25], ['C5',0.25], ['A4',0.5],  ['C4',0.25], ['E4',0.25], ['A4',0.25], ['B4',0.5],
    ['E4',0.25], ['C5',0.25], ['B4',0.25], ['A4',0.75]
]

songs = [{ "name": "Für Elise (Full Theme)", "melody": furElise_Full, "tempo": 0.31 }]

# ===== 게임 변수 =====
game_state = "MENU"
obstacles = []
audio_queue = []
perfect, good, miss, combo, maxCombo, score = 0, 0, 0, 0, 0, 0
start_time = 0
song_duration = 0

judge_text = ""
judge_color = (80, 80, 80)
judge_time = 0

is_ducking = False

def generate_game_data(song_data):
    generated_obstacles = []
    audio_schedule = []
    t = 2.5 

    for note, beat in song_data["melody"]:
        dur = beat * song_data["tempo"] * 4
        freq = NOTE_FREQ.get(note, 440)
        
        if freq:
            audio_schedule.append({
                "play_time": t,
                "sound": generate_tone_sound(freq, dur * 0.85)
            })

        spawn_x = DINO_X + (t * HURDLE_SPEED)
        generated_obstacles.append({
            "initial_x": spawn_x,
            "target_time": t,
            "hit": False,
            "done": False
        })
        t += dur
        
    return generated_obstacles, audio_schedule, t + 1.5

def start_game():
    global obstacles, audio_queue, song_duration, start_time, game_state
    global perfect, good, miss, combo, maxCombo, score, judge_text, is_ducking
    
    perfect = good = miss = combo = maxCombo = score = 0
    judge_text = ""
    is_ducking = False
    
    obstacles, audio_queue, song_duration = generate_game_data(songs[0])
    start_time = time.time()
    game_state = "PLAYING"

def trigger_judge(text, color):
    global judge_text, judge_color, judge_time
    judge_text = text
    judge_color = color
    judge_time = time.time()

# ===== 🦖 공룡 드로우 함수 =====
def draw_dino(surface, x, y, ducking):
    color = (80, 80, 80)
    bg_color = (247, 247, 247)
    
    if ducking:
        pygame.draw.rect(surface, color, (x - 6, y - 24, 38, 16))      
        pygame.draw.rect(surface, color, (x + 20, y - 24, 16, 12))     
        pygame.draw.rect(surface, color, (x - 12, y - 20, 8, 8))       
        pygame.draw.rect(surface, bg_color, (x + 28, y - 22, 3, 3))    
        
        step = int(time.time() * 16) % 2
        if step == 0:
            pygame.draw.rect(surface, color, (x + 4, y - 8, 4, 8))
            pygame.draw.rect(surface, color, (x + 18, y - 8, 4, 4))
        else:
            pygame.draw.rect(surface, color, (x + 4, y - 8, 4, 4))
            pygame.draw.rect(surface, color, (x + 18, y - 8, 4, 8))
    else:
        pygame.draw.rect(surface, color, (x, y - 40, 24, 26))      
        pygame.draw.rect(surface, color, (x + 12, y - 56, 22, 18)) 
        pygame.draw.rect(surface, color, (x - 6, y - 34, 8, 12))   
        pygame.draw.rect(surface, bg_color, (x + 18, y - 52, 4, 4)) 
        
        step = int(time.time() * 12) % 2
        if step == 0:
            pygame.draw.rect(surface, color, (x + 4, y - 14, 4, 14))
            pygame.draw.rect(surface, color, (x + 14, y - 14, 4, 8))
        else:
            pygame.draw.rect(surface, color, (x + 4, y - 14, 4, 8))
            pygame.draw.rect(surface, color, (x + 14, y - 14, 4, 14))

# ===== 🚧 [완전 개편] 똑바로 서 있는 묵직한 고높이 스탠드 철봉 그리기 =====
def draw_high_bar(surface, x, y):
    """바닥에서 위로 솟아있고 가로 바가 길어져 통과 시간이 늘어난 진짜 철봉"""
    bar_color = (80, 80, 80)
    pillar_color = (140, 140, 140)
    
    # 철봉 가로 너비를 40 -> 65픽셀로 대폭 확장 (공룡 위를 통과하는 시간이 시각적으로 확 길어짐!)
    bar_width = 65
    bar_height = 12  # 두께도 8 -> 12픽셀로 묵직하게 두꺼워짐
    bar_top_y = y - 54 # 서 있는 공룡 머리(y - 56)에 직격하는 위협적인 높이 설정
    
    # 1. 바닥에서 똑바로 솟아오른 세로 기둥 2개 (좌측 기둥, 우측 기둥)
    pygame.draw.rect(surface, pillar_color, (x, bar_top_y, 4, y - bar_top_y))
    pygame.draw.rect(surface, pillar_color, (x + bar_width - 4, bar_top_y, 4, y - bar_top_y))
    
    # 2. 기둥 꼭대기에 가로질러 놓인 묵직한 가로 철봉 바
    pygame.draw.rect(surface, bar_color, (x - 2, bar_top_y, bar_width + 4, bar_height), border_radius=3)

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
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    start_game()
            elif game_state == "RESULT":
                if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]:
                    game_state = "MENU"

    # 2. 실시간 조작 및 노트 판정
    if game_state == "PLAYING":
        pygame_keys = pygame.key.get_pressed()
        keys_to_check = [pygame.K_SPACE, pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k, pygame.K_DOWN]
        current_press_state = any(pygame_keys[k] for k in keys_to_check)
        
        if current_press_state and not is_ducking:
            is_ducking = True
            
            closest = None
            closest_dist = float('inf')
            for obs in obstacles:
                if not obs["hit"] and not obs["done"]:
                    dist = abs(current_time_sec - obs["target_time"])
                    if dist < closest_dist:
                        closest_dist = dist
                        closest = obs
            
            if closest and closest_dist < 0.22:
                closest["hit"] = True
                closest["done"] = True
                if closest_dist < 0.08:
                    perfect += 1; score += 300; combo += 1
                    trigger_judge('PERFECT', (50, 160, 50))
                else:
                    good += 1; score += 100; combo += 1
                    trigger_judge('GOOD', (160, 160, 50))
                if combo > maxCombo: maxCombo = combo

        elif not current_press_state and is_ducking:
            is_ducking = False

        # 오디오 재생
        for audio in audio_queue:
            if not audio.get("played", False) and current_time_sec >= audio["play_time"]:
                audio["sound"].play()
                audio["played"] = True

        # 장애물 위치 동기화 및 미스 판단
        for obs in obstacles:
            if obs["done"]: continue
            
            obs_x = obs["initial_x"] - (current_time_sec * HURDLE_SPEED)
            
            # 숙이지 않고 서 있을 때 철봉 바의 시작점이 공룡 앞머리 판정영역에 충돌하면 부딪힘(MISS)
            if obs_x < DINO_X + 12 and not obs["hit"]:
                obs["done"] = True
                miss += 1; combo = 0
                trigger_judge('MISS', (200, 50, 50))

        if current_time_sec > song_duration:
            game_state = "RESULT"

    # 3. 그래픽 렌더링
    screen.fill((247, 247, 247)) 
    
    if game_state == "MENU":
        screen.fill((40, 40, 45))
        title_surf = FONT_ORBITRON.render("Rex Rhythm : High Bar Dodge", True, (255, 215, 0))
        info_surf = FONT_ORBITRON.render("Press SPACEBAR to Play Full Song", True, (220, 220, 220))
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 140))
        screen.blit(info_surf, (WIDTH//2 - info_surf.get_width()//2, 200))

    elif game_state == "PLAYING":
        # 바닥 평행선
        pygame.draw.line(screen, (80, 80, 80), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)
        
        # 바닥 모래 데코 도트
        for dx in [80, 220, 360, 500]:
            pygame.draw.line(screen, (190, 190, 190), (dx, GROUND_Y + 6), (dx + 8, GROUND_Y + 6), 1)

        # 장애물 렌더링 (똑바로 서 있는 와이드 스탠드 철봉)
        for obs in obstacles:
            if obs["done"]: continue
            obs_x = obs["initial_x"] - (current_time_sec * HURDLE_SPEED)
            if -100 < obs_x < WIDTH + 50:
                draw_high_bar(screen, obs_x, GROUND_Y)

        # 공룡 캐릭터 렌더링
        draw_dino(screen, DINO_X, GROUND_Y, is_ducking)

        # UI 스코어 및 판정 보드 표기
        score_surf = FONT_ORBITRON.render(f"SCORE: {score}", True, (80, 80, 80))
        screen.blit(score_surf, (20, 20))
        
        if judge_text and (time.time() - judge_time < 0.45):
            j_surf = FONT_JUDGE.render(judge_text, True, judge_color)
            screen.blit(j_surf, (WIDTH//2 - j_surf.get_width()//2, 70))
            if combo > 1:
                c_surf = FONT_COMBO.render(f"{combo} COMBO", True, (120, 100, 240))
                screen.blit(c_surf, (WIDTH//2 - c_surf.get_width()//2, 125))

    elif game_state == "RESULT":
        screen.fill((35, 35, 40))
        res_title = FONT_ORBITRON.render("★ SONG CLEAR ★", True, (255, 215, 0))
        score_res = FONT_ORBITRON.render(f"FINAL SCORE : {score}", True, (220, 220, 220))
        stats_res = FONT_ORBITRON.render(f"PERFECT: {perfect}  |  GOOD: {good}  |  MISS: {miss}", True, (170, 170, 170))
        retry_surf = FONT_ORBITRON.render("PRESS SPACEBAR TO RETURN", True, (200, 200, 200))
        
        screen.blit(res_title, (WIDTH//2 - res_title.get_width()//2, 90))
        screen.blit(score_res, (WIDTH//2 - score_res.get_width()//2, 150))
        stats_surf_x = WIDTH//2 - stats_res.get_width()//2
        screen.blit(stats_res, (stats_surf_x, 190))
        screen.blit(retry_surf, (WIDTH//2 - retry_surf.get_width()//2, HEIGHT - 90))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
