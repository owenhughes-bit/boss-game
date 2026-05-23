import pygame
import sys #need it for when you want to quit the game
import random

WIDTH = 800
HEIGHT = 500
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (40, 40, 50)
RED   = (220, 60, 60)
BLUE  = (60, 120, 220)
GREEN = (60, 200, 100)
GRAVITY = 0.5
FLOOR = 400
BOSS_CHASE_DISTANCE = 300
BOSS_RETREAT_DISTANCE = 120
BOSS_WALK_SPEED = 2
BOSS_RETREAT_SPEED = 1.5

pygame.init() #Wakes up pygame

clock = pygame.time.Clock()

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED, vsync=1)
pygame.display.set_caption("Boss fight")

player = {
    "rect": pygame.Rect(150, 300, 50, 80),
    "color": BLUE,
    "hp": 100,
    "max_hp": 100,
    "vel_y": 0,
    "vel_x": 0,
    "onGround": False,
    "attacking": False,
    "attack_type": None,
    "attack_timer": 0,
    "parry_active": False,
    "parry_timer": 0,
    "invincible_timer": 0,
    "facing": 'right',
    "parry_used": False,
    "hit_flash": 0,
    "parry_recovery_timer": 0,
    "attack_landed": False,
    "recovery_timer": 0,
}
boss = {
    "rect": pygame.Rect(600, FLOOR - 90, 60, 90),
    "color": RED,
    "hp": 200,
    "max_hp": 200,
    "hit_cooldown": 0,
    "state": 'idle',
    "state_timer": 90,
    "attack_type": None,
    "facing": 'left',
    'vel_x': 0,
    "current_combo": [],
    "combo_index": 0,
    "hit_flash": 0,
}

move_counts = {
    "light": 0,
    "heavy": 0,
    "parry": 0,
    "jump_attack": 0,
}

patterns = {
    "after_boss_recovery": [],
    "after_boss_lunge": [],
    "at_close_range": [],
    "at_far_range": [],
    "after_jumping": [],
    "after_taking_damage": [],
    "response_to_windup": [],
    "last_move": None,
}
ATTACK_DATA = {
    "light": {"damage": 10, "width": 40, "height": 20, "active_frames": (5, 15)},
    "heavy": {"damage": 25, "width": 60, "height": 30, "active_frames": (10, 35)},
    "jump_attack": {"damage": 15, "width": 50, "height": 25, "active_frames": (5, 20)},
}
BOSS_ATTACKS = {
    "slash": {"damage": 15, "width": 70, "height": 30, "windup": 40, "active": 15, "recovery": 30},
    "lunge": {"damage": 25, "width": 70, "height": 40, "windup": 60, "active": 20, "recovery": 45},
    "jab": {"damage": 10, "width": 50, "height": 25, "windup": 20, "active": 10, "recovery": 20},
    "slam": {"damage": 20, "width": 80, "height": 50, "windup": 50, "active": 20, "recovery": 40},
    "spin": {"damage": 18, "width": 70, "height": 35, "windup": 45, "active": 25, "recovery": 35},
    "feint": {"damage": 0, "width": 0, "height": 0, "windup": 35, "active": 1, "recovery": 25},
}
BOSS_COMBOS = {
    "default": [
        ["jab", "slash"],
        ["slash", "lunge"],
        ["jab", "jab", "slam"],
        ["spin", "slash"],
        ["lunge", "slam"],
    ],
    "counter_light": [
        ["spin", "lunge"],
        ["spin", "slash", "jab"],
        ["jab", "spin", "slam"],
    ],
    "counter_heavy": [
        ["jab", "jab", "slash"],
        ["jab", "lunge"],
        ["jab", "jab", "jab"],
    ],
    "counter_parry": [
        ["feint", "lunge"],
        ["feint", "slam"],
        ["feint", "jab", "slash"],
    ],
    "counter_jump": [
        ["slam", "slash"],
        ["slam", "lunge"],
        ["slam", "jab", "slam"],
    ],
}

def choose_combo(move_counts):

    total = sum(move_counts.values())
    if (total < 20):
        return random.choice(BOSS_COMBOS["default"])
    
    light_pct = move_counts['light'] / total
    heavy_pct = move_counts['heavy'] / total
    parry_pct = move_counts['parry'] / total
    jump_pct = move_counts['jump_attack'] / total

    if (light_pct > 0.4):
        return random.choice(BOSS_COMBOS["counter_light"])
    elif (heavy_pct > 0.3):
        return random.choice(BOSS_COMBOS["counter_heavy"])
    elif (parry_pct > 0.3):
        return random.choice(BOSS_COMBOS["counter_parry"])
    elif (jump_pct > 0.3):
        return random.choice(BOSS_COMBOS["counter_jump"])
    else:
        return random.choice(BOSS_COMBOS["default"])

def record_pattern(pattern_key, move, max_history=20):
        patterns[pattern_key].append(move)
        if (len(patterns[pattern_key]) > max_history):
            patterns[pattern_key].pop(0)

def get_dominant(pattern_list):
        if not pattern_list:
            return None
        return max(set(pattern_list), key=pattern_list.count) #finds the most common move in a pattern list

def draw_health_bar(surface, x, y, current, maxiumum, width=200, height=20, color=GREEN):
    ratio = current / maxiumum
    pygame.draw.rect(surface, (80, 80, 80), (x, y, width, height)) #Background Bar
    pygame.draw.rect(surface, color, (x, y, int(width*ratio), height)) #Current hp bar
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 2) #border

def draw_end_screen(surface, message, color):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    font_big = pygame.font.SysFont("monospace", 64, bold=True)
    font_small = pygame.font.SysFont("monospace", 24)

    text = font_big.render(message, True, color)
    subtext = font_small.render("Press R to restart or Q to quit", True, WHITE)

    surface.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 60))
    surface.blit(subtext, (WIDTH//2 - subtext.get_width()//2, HEIGHT//2 + 20))
    

running = True
game_state = "playing"
shake_duration = 0
shake_intensity = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if (event.key == pygame.K_q):
                running = False
            if event.key == pygame.K_r and game_state != 'playing':
                #Resets Everything
                player['hp'] = player['max_hp']
                player['rect'].topleft = (150, FLOOR - 80)
                player['vel_x'] = 0
                player['vel_y'] = 0
                player['attacking'] = False
                player['attack_type'] = None
                player['attack_timer'] = 0
                player['parry_active'] = False
                player['parry_timer'] = 0
                player['invincible_timer'] = 0
                player['parry_used'] = False
                boss['hp'] = boss['max_hp']
                boss['rect'].topleft = (600, FLOOR - 90)
                boss['state'] = 'idle'
                boss['state_timer'] = 90
                boss['vel_x'] = 0
                boss['color'] = RED
                move_counts['light'] = 0
                move_counts['heavy'] = 0
                move_counts['parry'] = 0
                move_counts['jump_attack'] = 0
                game_state = "playing"

            if (game_state == "playing"):    
                if (event.key == pygame.K_z and not player['attacking'] and player['onGround'] and not player['parry_active'] and player['recovery_timer'] == 0):
                    player['attacking'] = True
                    player['attack_type'] = "light"
                    player['attack_timer'] = 20
                    player['attack_landed'] = True
                    move_counts['light'] += 1
                    distance = abs(player['rect'].centerx - boss['rect'].centerx)
                    if (distance < 150):
                        record_pattern('at_close_range', 'light')
                    else:
                        record_pattern('at_far_range', 'light')
                if (event.key == pygame.K_x and not player['attacking'] and player['onGround'] and not player['parry_active'] and player['recovery_timer'] == 0):
                    player['attacking'] = True
                    player['attack_type'] = "heavy"
                    player['attack_timer'] = 40
                    player['attack_landed'] = True

                    move_counts['heavy'] += 1
                if (event.key == pygame.K_c and not player['attacking'] and player['parry_recovery_timer'] == 0):
                    player['parry_active'] = True
                    player['parry_timer'] = 30
                    move_counts['parry'] += 1
                if (event.key == pygame.K_SPACE and not player['onGround'] and not player['attacking'] and not player['parry_active'] and player['recovery_timer'] == 0):
                    player['attacking'] = True
                    player['attack_type'] = "jump_attack"
                    player['attack_timer'] = 30
                    player['attack_landed'] = True
                    move_counts['jump_attack'] += 1
    
    canvas = pygame.Surface((WIDTH, HEIGHT))
    canvas.fill(GRAY)
    shake_x, shake_y = 0,0
    if shake_duration > 0:
        shake_x = random.randint(-shake_intensity, shake_intensity)
        shake_y = random.randint(-shake_intensity, shake_intensity)
        shake_duration -= 1
    screen_offset = (shake_x, shake_y)
    pygame.draw.rect(canvas, (100, 100, 110), (0, FLOOR, WIDTH, HEIGHT-FLOOR))
    draw_health_bar(canvas, 20, HEIGHT - 40, player['hp'], player['max_hp'], color=GREEN) #Player health bar - bottom left
    draw_health_bar(canvas, WIDTH//2 - 150, 20, boss['hp'], boss['max_hp'], width = 300, color = RED)

    if (game_state == "playing"):
        #Movement
        keys = pygame.key.get_pressed()
        if (player['attacking']):
            move_speed = 1.3
        else:
            move_speed = 5

        if (keys[pygame.K_LEFT] and player['rect'].left > 0):
            player["rect"].x -= move_speed
            if not player['attacking']:
                player['facing'] = 'left'
        if (keys[pygame.K_RIGHT] and player['rect'].right < WIDTH):
            player["rect"].x += move_speed
            if not player['attacking']:
                player['facing'] = 'right'
        if (keys[pygame.K_UP] and player['onGround']):
            player['vel_y'] = -12
        
        player['vel_y'] += GRAVITY
        player['rect'].y += player['vel_y']
        if (player['rect'].bottom >= FLOOR):
            player['rect'].bottom = FLOOR
            player['vel_y'] = 0
            player['onGround'] = True
        else:
            player['onGround'] = False
        
        #Fighting
        if (player['attack_timer'] > 0):
            player['attack_timer'] -= 1
        if player['attack_timer'] == 0 and player['attacking']:
            recovery_map = {"light": 8, "heavy": 18, "jump_attack": 10}
            player['recovery_timer'] = recovery_map.get(player['attack_type'], 8)
            player['attacking'] = False
            player['attack_type'] = None
        if player['recovery_timer'] > 0:
            player['recovery_timer'] -= 1
        if (player['parry_timer'] > 0):
            player['parry_timer'] -= 1
        else:
            if player['parry_active']:
                if not player['parry_used']:
                    player['parry_recovery_timer'] = 25
                    print("Parry whiffed!")
                player['parry_active'] = False
                player['parry_used'] = False
        if player['parry_recovery_timer'] > 0:
            player['parry_recovery_timer'] -= 1
        if (boss['hit_cooldown'] > 0):
            boss['hit_cooldown'] -= 1
        if (boss['vel_x'] > 0):
            boss['vel_x'] -= 0.5
        elif (boss['vel_x'] < 0):
            boss['vel_x'] += 0.5
        player['rect'].x += player['vel_x']
        if player['vel_x'] > 0:
            player['vel_x'] -= 0.8
        elif player['vel_x'] < 0:
            player['vel_x'] += 0.8
        if abs(player['vel_x']) < 0.8:
            player['vel_x'] = 0
        if player['rect'].left < 0:
            player['rect'].left = 0
        if player['rect'].right > WIDTH:
            player['rect'].right = WIDTH
        if player['hit_flash'] > 0:
            player['hit_flash'] -= 1
        if boss['hit_flash'] > 0:
            boss['hit_flash'] -= 1

        if player['attacking'] and player['attack_type'] in ATTACK_DATA:
            attack = ATTACK_DATA[player['attack_type']]
            frames_elapsed = ({"light": 20, "heavy": 40, "jump_attack": 30}[player['attack_type']] - player["attack_timer"])
            active_start, active_end = attack['active_frames']

            if (active_start <= frames_elapsed <= active_end):
                if (player['facing'] == 'right'):
                    hitbox = pygame.Rect(
                        player['rect'].right, #starts the the rightmost of the player
                        player['rect'].y+10,
                        attack['width'],
                        attack['height'],
                    )
                else:
                    hitbox = pygame.Rect(
                        player['rect'].left - attack['width'],
                        player['rect'].y+10,
                        attack['width'],
                        attack['height'],
                    )
                
                if (hitbox.colliderect(boss['rect']) and boss["hit_cooldown"] == 0): #Checks if the two hitboxes are overlapping
                    boss['hp'] -= attack['damage']
                    boss['hit_cooldown'] = {"light": 20, "heavy": 40, "jump_attack": 30}[player['attack_type']]
                    boss['hit_flash'] = 10
                    player['attack_landed'] = True
                    if (player['attack_type'] == 'heavy'):
                        shake_duration = 8
                        shake_intensity = 4
                    print(f"{player['attack_type']} hit! Boss hp: {boss['hp']}")
                
                pygame.draw.rect(canvas, GREEN, hitbox, 2)
                
        #Boss State Machine
        boss["state_timer"] -= 1
        if (boss['state'] == 'idle'):
            if (player['rect'].centerx < boss['rect'].centerx): #ensures the boss always faces the character
                boss['facing'] = 'left'
            else:
                boss['facing'] = 'right'

            distance = abs(player['rect'].centerx - boss['rect'].centerx)

            if (distance > BOSS_CHASE_DISTANCE):
                if boss['facing'] == 'left':
                    boss['rect'].x -= BOSS_WALK_SPEED
                else:
                    boss['rect'].x += BOSS_WALK_SPEED

            if (distance < BOSS_RETREAT_DISTANCE):
                if boss['facing'] == 'left':
                    boss['rect'].x += BOSS_RETREAT_SPEED
                else:
                    boss['rect'].x -= BOSS_RETREAT_SPEED
            
            if boss['rect'].left < 0:
                boss['rect'].left = 0
            if boss['rect'].right > WIDTH:
                boss['rect'].right = WIDTH
            
            if (boss['state_timer'] <= 0):
                boss['current_combo'] = choose_combo(move_counts)
                boss['combo_index'] = 0
                boss['state'] = 'windup'
                boss['attack_type'] = boss['current_combo'][0]
                boss['state_timer'] = BOSS_ATTACKS[boss['attack_type']]['windup']

        elif (boss['state'] == 'windup'):
            #Change color of the boss when it is about to attack
            boss['color'] = WHITE if boss['state_timer'] % 6 < 3 else RED #makes it flash
            
            if boss['state_timer'] <= 0:
                boss['state'] = 'attacking'
                boss['attack_type'] = boss['current_combo'][boss['combo_index']]
                boss['state_timer'] = BOSS_ATTACKS[boss['attack_type']]['active']

        elif (boss['state'] == 'attacking'):
            attack = BOSS_ATTACKS[boss['attack_type']]

            #lunge movement
            if boss['attack_type'] == 'lunge':
                boss['vel_x'] = -8 if boss['facing'] == 'left' else 8
            else:
                boss['vel_x'] = 0
            
            boss['rect'].x += boss['vel_x']

            if boss['rect'].left < 0:
                boss['rect'].left = 0
            if boss['rect'].right > WIDTH:
                boss['rect'].right = WIDTH

            if (boss['facing'] == 'left'):
                boss_hitbox = pygame.Rect(
                    boss['rect'].left - attack['width'],
                    boss['rect'].y + 10,
                    attack['width'],
                    attack['height'],
                )
            else:
                boss_hitbox = pygame.Rect(
                    boss['rect'].right,
                    boss['rect'].y + 10,
                    attack['width'],
                    attack['height'],
                )
            if (boss['attack_type'] == 'spin'):
                boss_hitbox = pygame.Rect(
                    boss['rect'].left - attack['width'],
                    boss['rect'].y+10,
                    attack['width'] * 2 + boss['rect'].width,
                    attack['height']
                )
            if (boss['attack_type'] == 'slam'):
                boss_hitbox = pygame.Rect(
                    boss['rect'].left - 20,
                    boss['rect'].bottom,
                    boss['rect'].width + 40,
                    attack['height']
                )

            pygame.draw.rect(canvas, RED, boss_hitbox, 2)

            if boss_hitbox.colliderect(player['rect']) and player['invincible_timer'] == 0:
                if player['parry_active'] and not player['parry_used']:
                    player['parry_used'] = True
                    if player['parry_timer'] > 22:
                        print("Perfect Parry! Boss Stunned!")
                        boss['state_timer'] = 90
                        boss['state'] = 'stunned'
                        boss['vel_x'] = 0
                        boss['color'] = RED
                    else:
                        print('Regular Parry! Damage Blocked')
                elif not player['parry_active']:
                    player['hp'] -= attack['damage']
                    player['invincible_timer'] = 40
                    player['hit_flash'] = 10
                    if boss['facing'] == 'left':
                        player['vel_x'] = -8
                    else:
                        player['vel_x'] = 8
                    shake_duration = 12
                    shake_intensity = 6
                    player['vel_y'] = -5
                    print(f"Player hit! HP: {player['hp']}")
            
            if boss['state_timer'] <= 0:
                boss['vel_x'] = 0
                boss['state'] = 'recovery'
                boss['color'] = RED
                boss['state_timer'] = BOSS_ATTACKS[boss['attack_type']]['recovery']
        
        elif (boss['state'] == 'recovery'):
            if boss['state_timer'] <= 0:
                boss['combo_index'] += 1
                if (boss['combo_index'] < len(boss['current_combo'])):
                    boss['attack_type'] = boss['current_combo'][boss['combo_index']]
                    boss['state_timer'] = BOSS_ATTACKS[boss['attack_type']]['windup']
                    boss['state'] = 'windup'
                else:
                    boss['state'] = 'idle'
                    boss['state_timer'] = random.randint(60, 120)
        
        elif (boss['state'] == 'stunned'):
            boss['color'] = WHITE
            boss['vel_x'] = 0
            if boss['state_timer'] <= 0:
                boss['state'] = 'idle'
                boss['state_timer'] = random.randint(45, 75)
                boss['color'] = RED
        
        if (player['invincible_timer'] > 0):
            player['invincible_timer'] -= 1

        if player['hp'] <= 0:
            game_state = "lose"
        if boss['hp'] <= 0:
            game_state = "win"
    
    player_color = RED if player['hit_flash'] > 0 else player['color']
    boss_color = GREEN if boss['hit_flash'] > 0 else boss['color']
    pygame.draw.rect(canvas, player_color, player["rect"])
    pygame.draw.rect(canvas, boss_color, boss['rect'])

    if game_state == "lose":
        draw_end_screen(canvas, "YOU DIED", RED)
    elif game_state == "win":
        draw_end_screen(canvas, "VICTORY", GREEN)

    screen.blit(canvas, screen_offset)
    pygame.display.flip() #Displays everything written on screen
    clock.tick(FPS) #sets FPS cap so that time isn't faster based on processing power

print(move_counts)
pygame.quit()
sys.exit()