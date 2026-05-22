import pygame
import math
import time

# ===== 초기화 및 설정 =====
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

WIDTH, HEIGHT = 640, 400  
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🦖 Rhythm Dino - Perfect Sync")
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
DINO_X = 100        # 공룡의 X 위치
GROUND_Y = 280      # 바닥 높이
HURDLE_SPEED = 350  # 장애물이 왼쪽으로 이동하는 속도 (픽셀/초)

# ===== 오디오 주파수 합성 =====
NOTE_FREQ = {
    'C4':261.63, 'E4':329.63, 'G4':392.00, 'B4':493.88, 
    'C5':523.25, 'D5':587.33, 'E5':659.25, 'F5':698.46, 'G5':783.99
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

# ===== 엘리제를 위하여 (빠른 템포 직관적 박자 배열) =====
furElise = [
    ['E5',0.25], ['D5',0.25], ['E5',0.25], ['D5',0.25], ['E5',0.25], ['B4',0.25], ['D5',0.25], ['C5',0.25], ['A4',0.5],
    ['C4',0.25], ['E4',0.25], ['A4',0.25], ['B4',0.5],  ['E4',0.25], ['G4',0.25], ['B4',0.25], ['C5',0.5],
    ['E5',0.25], ['D5',0.25], ['E5',0.25], ['D5',0.25], ['E5',0.25], ['B4',0.25], ['D5',0.25], ['C5',0.25], ['A4',0.5]
]

songs = [{ "name": "Für Elise", "melody": furElise, "tempo": 0.30 }]

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

# 공룡 점프 관련 변수
dino_jump_y = 0
dino_jump_speed = 0
GRAVITY = 0.6            # 떨어지는 중력 무게감
JUMP_POWER = -11.5       # 점프 세기

def generate_game_data(song_data):
    generated_obstacles = []
    audio_schedule = []
    
    # 대기 시간(3초) 후에 첫 장애물이 공룡에게 도달하도록 설정
    t = 3.0 

    for note, beat in song_data["melody"]:
        dur = beat * song_data["tempo"] * 4
        freq = NOTE_FREQ.get(note, 440)
        
        if freq:
            audio_schedule.append({
                "play_time": t,
                "sound": generate_tone_sound(freq, dur * 0.85)
            })

        # 장애물의 초기 스폰 위치 X 계산 (t 초일 때 정확히 DINO_X에 도달하게 역산)
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
    global perfect, good, miss, combo, maxCombo, score, judge_text, dino_jump_y, dino_jump_speed
    
    perfect = good = miss = combo = maxCombo = score = 0
    judge_text = ""
    dino_jump_y = 0
    dino_jump_speed = 0
    
    obstacles, audio_queue, song_duration = generate_game_data(songs[0])
    start_time = time.time()
    game_state = "PLAYING"

def trigger_judge(text, color):
    global judge_text, judge_color, judge_time
    judge_text = text
    judge_color = color
    judge_time = time.time()

# ===== 🦖 그래픽 그리기 함수 =====
def draw_dino(surface, x, y):
    pygame.draw.rect(surface, (80, 80, 80), (x, y - 40, 24, 26))      
    pygame.draw.rect(surface, (80, 80, 80), (x + 12, y - 56, 22, 18)) 
    pygame.draw.rect(surface, (80, 80, 80), (x - 6, y - 34, 8, 12))   
    pygame.draw.rect(surface, (247, 247, 247), (x + 18, y - 52, 4, 4)) 
    
    if y == GROUND_Y:
        step = int(time.time() * 12) % 2
        if step == 0:
            pygame.draw.rect(surface, (80, 80, 80), (x + 4, y - 14, 4, 14))
            pygame.draw.rect(surface, (80, 80, 80), (x + 14, y - 14, 4, 8))
        else:
            pygame.draw.rect(surface, (80, 80, 80), (x + 4, y - 14, 4, 8))
            pygame.draw.rect(surface, (80, 80, 80), (x + 14, y - 14, 4, 14))
    else:
        pygame.draw.rect(surface, (80, 80, 80), (x + 4, y - 14, 4, 10))
        pygame.draw.rect(surface, (80, 80, 80), (x + 14, y - 14, 4, 10))

def draw_fence_hurdle(surface, x, y):
    pygame.draw.line(surface, (100, 100, 100), (x, y - 28), (x + 65, y - 28), 2)
    pygame.draw.line(surface, (100, 100, 100), (x, y - 18), (x + 65, y - 18), 2)
    pygame.draw.line(surface, (100, 100, 100), (x, y - 8), (x + 65, y - 8), 2)
    for px in [x, x + 20, x + 40, x + 60]:
        pygame.draw.rect(surface, (247, 247, 247), (px - 1, y - 36, 6, 36)) 
        pygame.draw.rect(surface, (100, 100, 100), (px, y - 35, 4, 35), width=1)

# ===== 메인 루프 =====
running = True
while running:
    current_time_sec = time.time() - start_time if game_state == "PLAYING" else 0
    
    # 1. 키보드 이벤트 입력 처리
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
                    
            elif game_state == "PLAYING":
                # ❗ [핵심 수정] 어떤 판정이든 상관없이 스페이스바/아무 키 누르면 즉시 무조건 점프 동작 발동!
                if event.key in [pygame.K_SPACE, pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]:
                    if dino_jump_y == 0: 
                        dino_jump_speed = JUMP_POWER
                    
                    # 가장 가까이 다가온 장애물 리듬 판정 검사
                    closest = None
                    closest_dist = float('inf')
                    for obs in obstacles:
                        if not obs["hit"] and not obs["done"]:
                            dist = abs(current_time_sec - obs["target_time"])
                            if dist < closest_dist:
                                closest_dist = dist
                                closest = obs
                    
                    if closest and closest_dist < 0.25:
                        closest["hit"] = True
                        closest["done"] = True
                        if closest_dist < 0.08:
                            perfect += 1; score += 300; combo += 1
                            trigger_judge('PERFECT', (50, 160, 50))
                        else:
                            good += 1; score += 100; combo += 1
                            trigger_judge('GOOD', (160, 160, 50))
                        if combo > maxCombo: maxCombo = combo

    # 2. 실시간 로직 업데이트
    if game_state == "PLAYING":
        # 오디오 큐 재생 싱크
        for audio in audio_queue:
            if not audio.get("played", False) and current_time_sec >= audio["play_time"]:
                audio["sound"].play()
                audio["played"] = True

        # 장애물 위치 갱신 및 미스 판정
        for obs in obstacles:
            if obs["done"]: continue
            
            # 실시간 동기화 위치 공식 계산
            obs_x = obs["initial_x"] - (current_time_sec * HURDLE_SPEED)
            
            # 플레이어가 제때 점프하지 못하고 울타리를 지나쳐 버렸을 때 (MISS)
            if obs_x < DINO_X - 10 and not obs["hit"]:
                obs["done"] = True
                miss += 1; combo = 0
                trigger_judge('MISS', (200, 50, 50))

        # 공룡 점프 중력 가속도 연산
        if dino_jump_y < 0 or dino_jump_speed != 0:
            dino_jump_y += dino_jump_speed
            dino_jump_speed += GRAVITY
            if dino_jump_y >= 0:
                dino_jump_y = 0
                dino_jump_speed = 0

        # 곡이 완전히 끝나면 결과 창 이동
        if current_time_sec > song_duration:
            game_state = "RESULT"

    # 3. 렌더링 화면 그리기
    screen.fill((247, 247, 247)) 
    
    if game_state == "MENU":
        screen.fill((40, 40, 45))
        title_surf = FONT_ORBITRON.render("🦖 DINO RHYTHM RUNNER", True, (255, 215, 0))
        info_surf = FONT_ORBITRON.render("Press SPACEBAR to Start Game", True, (220, 220, 220))
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 140))
        screen.blit(info_surf, (WIDTH//2 - info_surf.get_width()//2, 200))

    elif game_state == "PLAYING":
        # 바닥 평선 
        pygame.draw.line(screen, (80, 80, 80), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)
        
        # 미니 모래 장식
        for dx in [60, 200, 340, 480, 600]:
            pygame.draw.line(screen, (190, 190, 190), (dx, GROUND_Y + 6), (dx + 6, GROUND_Y + 6), 1)

        # 장애물 드로우
        for obs in obstacles:
            if obs["done"]: continue
            obs_x = obs["initial_x"] - (current_time_sec * HURDLE_SPEED)
            if -80 < obs_x < WIDTH + 50:
                draw_fence_hurdle(screen, obs_x, GROUND_Y)

        # 공룡 캐릭터 드로우 (점프 높이 반영)
        draw_dino(screen, DINO_X, GROUND_Y + dino_jump_y)

        # 점수 정보 상단 출력
        score_surf = FONT_ORBITRON.render(f"SCORE: {score}", True, (80, 80, 80))
        screen.blit(score_surf, (20, 20))
        
        # 판정 텍스트 연출
        if judge_text and (time.time() - judge_time < 0.5):
            j_surf = FONT_JUDGE.render(judge_text, True, judge_color)
            screen.blit(j_surf, (WIDTH//2 - j_surf.get_width()//2, 70))
            if combo > 1:
                c_surf = FONT_COMBO.render(f"{combo} COMBO", True, (100, 100, 220))
                screen.blit(c_surf, (WIDTH//2 - c_surf.get_width()//2, 125))

    elif game_state == "RESULT":
        screen.fill((30, 30, 35))
        res_title = FONT_ORBITRON.render("★ STAGE CLEAR ★", True, (255, 215, 0))
        score_res = FONT_ORBITRON.render(f"FINAL SCORE : {score}", True, (220, 220, 220))
        stats_res = FONT_ORBITRON.render(f"PERFECT: {perfect}  |  GOOD: {good}  |  MISS: {miss}", True, (170, 170, 170))
        retry_surf = FONT_ORBITRON.render("PRESS SPACE TO RETURN MENU", True, (200, 200, 200))
        
        screen.blit(res_title, (WIDTH//2 - res_title.get_width()//2, 90))
        screen.blit(score_res, (WIDTH//2 - score_res.get_width()//2, 150))
        screen.blit(stats_res, (WIDTH//2 - stats_res.get_width()//2, 190))
        screen.blit(retry_surf, (WIDTH//2 - retry_surf.get_width()//2, HEIGHT - 90))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
