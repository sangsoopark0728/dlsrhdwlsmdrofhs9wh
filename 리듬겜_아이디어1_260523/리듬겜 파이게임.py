import pygame
import math
import random
import time

# ===== 초기화 및 설정 =====
pygame.mixer.pre_init(44100, -16, 2, 512) # 사운드 레이턴시 최소화
pygame.init()

WIDTH, HEIGHT = 520, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎵 Rhythm Game - Python Edition")
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
KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
KEY_LABELS = ['D', 'F', 'J', 'K']
LANE_X = [0, 130, 260, 390]
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
    ['D5',0.25],['C5',0.25],['B4',0.5],['E4',0.25],['C5',0.25],['B4',0.25],['A4',0.75],['E5',0.25],
    ['D#5',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['B4',0.25],['D5',0.25],['C5',0.25],['A4',0.5],
    ['C4',0.25],['E4',0.25],['A4',0.25],['B4',0.5],['E4',0.25],['G#4',0.25],['B4',0.25],['C5',0.5],
    ['E4',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['B4',0.25],['D5',0.25],
    ['C5',0.25],['A4',0.5],['C4',0.25],['E4',0.25],['A4',0.25],['B4',0.5],['E4',0.25],['C5',0.25],
    ['B4',0.25],['A4',0.75],['A4',0.25],['E5',0.25],['A5',0.25],['E5',0.25],['A4',0.25],['E5',0.25],
    ['A5',0.25],['E5',0.25],['G#4',0.25],['E5',0.25],['G#5',0.25],['E5',0.25],['G#4',0.25],['E5',0.25],
    ['G#5',0.25],['E5',0.25],['A4',0.25],['E5',0.25],['A5',0.25],['E5',0.25],['B4',0.25],['E5',0.25],
    ['B5',0.25],['E5',0.25],['C5',0.25],['E5',0.25],['C6',0.25],['E5',0.25],['B4',0.25],['E5',0.25],
    ['B5',0.25],['E5',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['B4',0.25],
    ['D5',0.25],['C5',0.25],['A4',0.5],['C4',0.25],['E4',0.25],['A4',0.25],['B4',0.5],['E4',0.25],
    ['G#4',0.25],['B4',0.25],['C5',0.5],['E4',0.25],['E5',0.25],['D#5',0.25],['E5',0.25],['D#5',0.25],
    ['E5',0.25],['B4',0.25],['D5',0.25],['C5',0.25],['A4',0.5],['C4',0.25],['E4',0.25],['A4',0.25],
    ['B4',0.5],['E4',0.25],['C5',0.25],['B4',0.25],['A4',1.0]
]

nachtmusik = [
    ['G4',0.25],['D5',0.25],['G4',0.25],['D5',0.25],['G4',0.25],['D5',0.25],['G5',0.5],['A5',0.25],
    ['G5',0.25],['F#5',0.25],['G5',0.25],['A5',0.5],['D4',0.25],['A4',0.25],['D4',0.25],['A4',0.25],
    ['D4',0.25],['A4',0.25],['D5',0.5],['E5',0.25],['D5',0.25],['C#5',0.25],['D5',0.25],['E5',0.5],
    ['G4',0.25],['D5',0.25],['G4',0.25],['D5',0.25],['G4',0.25],['D5',0.25],['G5',0.5],['A5',0.25],
    ['G5',0.25],['F#5',0.25],['G5',0.25],['A5',0.5],['B4',0.25],['G5',0.25],['G5',0.25],['F#5',0.25],
    ['F#5',0.25],['E5',0.25],['E5',0.25],['D5',0.25],['C5',0.25],['B4',0.25],['A4',0.25],['G4',0.5],
    ['D5',0.5],['G5',0.5],['F#5',0.25],['E5',0.25],['D5',0.5],['C5',0.5],['B4',0.5],['A4',0.5],
    ['G4',0.5],['D5',0.25],['E5',0.25],['F#5',0.25],['G5',0.5],['A5',0.25],['B5',0.25],['A5',0.25],
    ['G5',0.5],['F#5',0.25],['G5',0.25],['A5',0.25],['D5',0.5],['E5',0.25],['F#5',0.25],['G5',0.25],
    ['A5',0.25],['B5',0.5],['G5',0.125],['F#5',0.125],['E5',0.125],['D5',0.125],['C5',0.125],
    ['B4',0.125],['A4',0.125],['G4',0.125],['F#4',0.125],['G4',0.125],['A4',0.125],['B4',0.125],
    ['C5',0.125],['D5',0.125],['E5',0.125],['F#5',0.125],['G4',0.25],['D5',0.25],['G4',0.25],
    ['D5',0.25],['G4',0.25],['D5',0.25],['G5',0.5],['A5',0.25],['G5',0.25],['F#5',0.25],['G5',0.25],
    ['A5',0.5],['D4',0.25],['A4',0.25],['D4',0.25],['A4',0.25],['D4',0.25],['A4',0.25],['D5',0.5],
    ['E5',0.25],['D5',0.25],['C#5',0.25],['D5',0.25],['E5',0.5],['G5',0.25],['F#5',0.25],['E5',0.25],
    ['D5',0.25],['C5',0.25],['B4',0.25],['A4',0.25],['G4',0.25],['G4',0.5],['D5',0.5],['G5',1.0]
]

songs = [
    { "name": "Für Elise", "composer": "Beethoven", "melody": furElise, "tempo": 0.32, "color": (255, 170, 51), "longColor": (255, 119, 0) },
    { "name": "Eine kleine Nachtmusik", "composer": "Mozart", "melody": nachtmusik, "tempo": 0.28, "color": (68, 170, 255), "longColor": (0, 102, 204) }
]

# ===== 게임 변수 상태 그룹 =====
game_state = "MENU" # MENU, PLAYING, RESULT
selected_song_idx = 0

notes = []
perfect, good, bad, miss, combo, maxCombo, score = 0, 0, 0, 0, 0, 0, 0
start_time = 0
song_duration = 0
current_song = None

holding_state = [False, False, False, False]
keys_pressed = [False, False, False, False]

judge_text = ""
judge_color = (255, 255, 255)
judge_time = 0

audio_queue = []

# ===== 게임 시스템 함수 =====
def generate_notes(song_data):
    global song_duration
    generated = []
    t = APPROACH_TIME
    last_lane = -1
    audio_schedule = []

    for note, beat in song_data["melody"]:
        dur = beat * song_data["tempo"] * 4
        min_dur = song_data["tempo"] * 0.7
        
        freq = NOTE_FREQ.get(note, 440)
        
        if freq:
            audio_schedule.append({
                "play_time": t,
                "sound": generate_tone_sound(freq, dur * 0.9)
            })

        if dur >= min_dur:
            if freq < 260: lane = 0
            elif freq < 400: lane = 1
            elif freq < 600: lane = 2
            else: lane = 3

            if lane == last_lane and random.random() < 0.45:
                lane = (lane + 1) % 4

            is_long = beat >= 0.5 and (
                (beat >= 0.75 and random.random() < 0.6) or
                (beat >= 0.5 and random.random() < 0.35)
            )
            end_time = t + dur * 0.85 if is_long else None

            generated.append({
                "lane": lane,
                "time": t,
                "endTime": end_time,
                "isLong": is_long,
                "hit": False,
                "done": False,
                "missed": False,
                "holdReleased": False
            })
            last_lane = lane
            
        t += dur
        
    song_duration = t + 1
    return generated, audio_schedule

def start_game(idx):
    global notes, audio_queue, perfect, good, bad, miss, combo, maxCombo, score
    global holding_state, keys_pressed, start_time, game_state, current_song, judge_text
    
    perfect = good = bad = miss = combo = maxCombo = score = 0
    holding_state = [False, False, False, False]
    keys_pressed = [False, False, False, False]
    judge_text = ""
    
    current_song = songs[idx]
    notes, audio_queue = generate_notes(current_song)
    
    start_time = time.time()
    game_state = "PLAYING"

def trigger_judge(text, color):
    global judge_text, judge_color, judge_time
    judge_text = text
    judge_color = color
    judge_time = time.time()

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
                    
            elif game_state == "PLAYING":  # 수정 완료된 부분
                pass 
                
            elif game_state == "RESULT":
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    game_state = "MENU"

    # 실시간 키 상태 동기화 (인게임 처리)
    if game_state == "PLAYING":
        pygame_keys = pygame.key.get_pressed()
        for i, key_code in enumerate(KEYS):
            if pygame_keys[key_code] and not keys_pressed[i]:
                keys_pressed[i] = True
                
                closest = None
                closest_dist = float('inf')
                for n in notes:
                    if n["lane"] == i and not n["hit"] and not n["done"]:
                        dist = abs(current_time_sec - n["time"])
                        if dist < closest_dist:
                            closest_dist = dist
                            closest = n
                            
                if closest and closest_dist < 0.28:
                    closest["hit"] = True
                    if closest["isLong"]:
                        holding_state[i] = True
                        
                    if closest_dist < 0.07:
                        perfect += 1; score += 300; combo += 1
                        trigger_judge('PERFECT', (128, 255, 128))
                    elif closest_dist < 0.16:
                        good += 1; score += 100; combo += 1
                        trigger_judge('GOOD', (255, 255, 128))
                    else:
                        bad += 1; score += 50; combo = 0
                        trigger_judge('BAD', (255, 128, 128))
                    if combo > maxCombo: maxCombo = combo
                    
                    if not closest["isLong"]:
                        closest["done"] = True

            elif not pygame_keys[key_code] and keys_pressed[i]:
                keys_pressed[i] = False
                if holding_state[i]:
                    holding_state[i] = False
                    
                    for n in notes:
                        if n["lane"] == i and n["hit"] and not n["holdReleased"] and not n["done"] and n["isLong"]:
                            remaining = n["endTime"] - current_time_sec
                            if remaining > 0.15:
                                n["holdReleased"] = True
                                n["done"] = True
                                n["missed"] = True
                                combo = 0
                                trigger_judge('MISS', (255, 68, 68))

    # 2. 게임 상태 업데이트 & 오디오 재생
    if game_state == "PLAYING":
        for audio in audio_queue:
            if not audio.get("played", False) and current_time_sec >= audio["play_time"]:
                audio["sound"].play()
                audio["played"] = True
                
        for n in notes:
            if n["done"]: continue
            head_y = (current_time_sec - (n["time"] - APPROACH_TIME)) * NOTE_SPEED
            
            if n["isLong"]:
                if n["hit"] and not n["holdReleased"]:
                    tail_y = (current_time_sec - (n["endTime"] - APPROACH_TIME)) * NOTE_SPEED
                    if tail_y >= JUDGE_Y - 24:
                        n["holdReleased"] = True
                        n["done"] = True
                        score += 200
                        trigger_judge('GREAT!', (128, 255, 255))
                else:
                    if head_y > JUDGE_Y + 20:
                        n["done"] = True
                        n["missed"] = True
                        miss += 1; combo = 0
                        trigger_judge('MISS', (255, 68, 68))
            else:
                if head_y > JUDGE_Y + 20 and not n["hit"]:
                    n["done"] = True
                    n["missed"] = True
                    miss += 1; combo = 0
                    trigger_judge('MISS', (255, 68, 68))

        if current_time_sec > song_duration + 2:
            game_state = "RESULT"

    # 3. 그래픽 렌더링
    screen.fill((10, 10, 26))
    
    if game_state == "MENU":
        title_surf = FONT_ORBITRON.render("🎹 SELECT MUSIC", True, (255, 215, 0))
        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 100))
        
        for idx, song in enumerate(songs):
            bg_color = (20, 30, 50) if idx == selected_song_idx else (13, 24, 42)
            border_color = (68, 102, 255) if idx == selected_song_idx else (34, 34, 51)
            
            rect_box = pygame.Rect(60, 200 + idx*110, 400, 90)
            pygame.draw.rect(screen, bg_color, rect_box, border_radius=10)
            pygame.draw.rect(screen, border_color, rect_box, width=2, border_radius=10)
            
            num_surf = FONT_ORBITRON.render(f"0{idx+1}", True, (68, 102, 255))
            name_surf = FONT_ORBITRON.render(song["name"], True, (255, 255, 255))
            sub_surf = FONT_ORBITRON.render(f"{song['composer']} · ~60s", True, (102, 102, 119))
            
            screen.blit(num_surf, (85, 230 + idx*110))
            screen.blit(name_surf, (150, 220 + idx*110))
            screen.blit(sub_surf, (150, 250 + idx*110))
            
        guide_surf = FONT_ORBITRON.render("KEYS: D F J K  |  PRESS ENTER TO PLAY", True, (100, 100, 120))
        screen.blit(guide_surf, (WIDTH//2 - guide_surf.get_width()//2, 550))

    elif game_state == "PLAYING":
        for i in range(4):
            if keys_pressed[i]:
                pygame.draw.rect(screen, (30, 45, 75), (LANE_X[i], 0, 130, HEIGHT))
            pygame.draw.line(screen, (26, 26, 46), (LANE_X[i]+130, 0), (LANE_X[i]+130, HEIGHT), 1)

        pygame.draw.line(screen, (255, 51, 51), (0, JUDGE_Y), (WIDTH, JUDGE_Y), 3)
        
        for n in notes:
            if n["done"]: continue
            head_y = (current_time_sec - (n["time"] - APPROACH_TIME)) * NOTE_SPEED
            if head_y < -100 or head_y > HEIGHT: continue
            
            color = current_song["color"]
            l_color = current_song["longColor"]
            
            if n["isLong"]:
                tail_y = (current_time_sec - (n["endTime"] - APPROACH_TIME)) * NOTE_SPEED
                if n["hit"] and not n["holdReleased"]:
                    body_top = max(0, tail_y)
                    body_bottom = JUDGE_Y - 24
                    if body_bottom > body_top:
                        pygame.draw.rect(screen, l_color, (LANE_X[n['lane']]+10, body_top, 110, body_bottom - body_top))
                    pygame.draw.rect(screen, color, (LANE_X[n['lane']]+10, JUDGE_Y - 24, 110, 24), border_radius=5)
                else:
                    body_top = tail_y
                    body_bottom = head_y
                    if body_bottom > body_top:
                        pygame.draw.rect(screen, l_color, (LANE_X[n['lane']]+10, body_top, 110, body_bottom - body_top))
                    pygame.draw.rect(screen, color, (LANE_X[n['lane']]+10, head_y, 110, 24), border_radius=5)
            else:
                pygame.draw.rect(screen, color, (LANE_X[n['lane']]+10, head_y, 110, 24), border_radius=5)

        for lane in range(4):
            if holding_state[lane]:
                pygame.draw.rect(screen, current_song["color"], (LANE_X[lane]+10, JUDGE_Y-20, 110, 40), width=2, border_radius=5)

        pygame.draw.rect(screen, (5, 5, 16), (0, 630, WIDTH, 90))
        pygame.draw.line(screen, (34, 34, 34), (0, 630), (WIDTH, 630), 2)
        
        for i in range(4):
            btn_y = 652 if keys_pressed[i] else 650
            btn_color = (40, 40, 60) if keys_pressed[i] else (20, 20, 20)
            pygame.draw.rect(screen, btn_color, (LANE_X[i]+10, btn_y, 110, 60), border_radius=8)
            pygame.draw.rect(screen, (102, 102, 255) if keys_pressed[i] else (51, 51, 51), (LANE_X[i]+10, btn_y, 110, 60), width=2, border_radius=8)
            
            lbl = FONT_ORBITRON.render(KEY_LABELS[i], True, (255, 255, 255))
            screen.blit(lbl, (LANE_X[i]+65 - lbl.get_width()//2, btn_y+30 - lbl.get_height()//2))

        progress_w = min(WIDTH, (current_time_sec / song_duration) * WIDTH)
        pygame.draw.rect(screen, (170, 68, 255), (0, 0, progress_w, 4))
        
        score_surf = FONT_ORBITRON.render(f"SCORE: {score}", True, (255, 255, 255))
        time_surf = FONT_ORBITRON.render(f"{int(current_time_sec)}s / {int(song_duration)}s", True, (150, 150, 150))
        screen.blit(score_surf, (15, 20))
        screen.blit(time_surf, (WIDTH - time_surf.get_width() - 15, 20))

        if judge_text and (time.time() - judge_time < 0.42):
            j_surf = FONT_JUDGE.render(judge_text, True, judge_color)
            screen.blit(j_surf, (WIDTH//2 - j_surf.get_width()//2, HEIGHT - 220))
            
            if combo > 1 and judge_text not in ['MISS', 'BAD']:
                c_surf = FONT_COMBO.render(f"{combo} COMBO", True, (255, 215, 0))
                screen.blit(c_surf, (WIDTH//2 - c_surf.get_width()//2, HEIGHT - 265))

    elif game_state == "RESULT":
        total_notes = perfect + good + bad + miss
        accuracy = (perfect * 100 + good * 60 + bad * 20) / (total_notes * 100) * 100 if total_notes > 0 else 0
        
        if accuracy >= 95: rank, rank_color = 'S', (255, 215, 0)
        elif accuracy >= 85: rank, rank_color = 'A', (128, 255, 128)
        elif accuracy >= 70: rank, rank_color = 'B', (102, 204, 255)
        elif accuracy >= 50: rank, rank_color = 'C', (255, 170, 68)
        else: rank, rank_color = 'D', (136, 136, 136)
        
        res_title = FONT_ORBITRON.render("★ RESULT ★", True, (255, 255, 255))
        rank_surf = FONT_RANK.render(rank, True, rank_color)
        
        screen.blit(res_title, (WIDTH//2 - res_title.get_width()//2, 50))
        screen.blit(rank_surf, (WIDTH//2 - rank_surf.get_width()//2, 100))
        
        details = [
            f"PERFECT : {perfect}",
            f"GOOD : {good}",
            f"BAD : {bad}",
            f"MISS : {miss}",
            f"MAX COMBO : {maxCombo}",
            f"TOTAL SCORE : {score}",
            f"ACCURACY : {accuracy:.1f}%"
        ]
        
        for i, text in enumerate(details):
            det_surf = FONT_ORBITRON.render(text, True, (200, 200, 220))
            screen.blit(det_surf, (WIDTH//2 - det_surf.get_width()//2, 260 + i * 35))
            
        retry_surf = FONT_ORBITRON.render("PRESS SPACEBAR TO RETURN", True, (255, 215, 0))
        screen.blit(retry_surf, (WIDTH//2 - retry_surf.get_width()//2, HEIGHT - 100))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
