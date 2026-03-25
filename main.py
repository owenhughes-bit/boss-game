import pygame
import sys #need it for when you want to quit the game

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
    "onGround": False,
    "attacking": False,
    "attack_type": None,
    "attack_timer": 0,
    "parry_active": False,
    "parry_timer": 0,
    "invincible_timer": 0,
}
boss = {
    "rect": pygame.Rect(600, 300, 60, 90),
    "color": RED,
    "hp": 200,
    "max_hp": 200,
    "hit_cooldown": 0,
}

move_counts = {
    "light": 0,
    "heavy": 0,
    "parry": 0,
    "jump_attack": 0,
}
ATTACK_DATA = {
    "light": {"damage": 10, "width": 40, "height": 20, "active_frames": (5, 15)},
    "heavy": {"damage": 25, "width": 60, "height": 30, "active_frames": (10, 35)},
    "jump_attack": {"damage": 15, "width": 50, "height": 25, "active_frames": (5, 20)},
}


running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if (event.key == pygame.K_z and not player['attacking'] and player['onGround'] and not player['parry_active']):
                player['attacking'] = True
                player['attack_type'] = "light"
                player['attack_timer'] = 20
                move_counts['light'] += 1
            if (event.key == pygame.K_x and not player['attacking'] and player['onGround'] and not player['parry_active']):
                player['attacking'] = True
                player['attack_type'] = "heavy"
                player['attack_timer'] = 40
                move_counts['heavy'] += 1
            if (event.key == pygame.K_c and not player['attacking']):
                player['parry_active'] = True
                player['parry_timer'] = 30
                move_counts['parry'] += 1
            if (event.key == pygame.K_SPACE and not player['onGround'] and not player['attacking'] and not player['parry_active']):
                player['attacking'] = True
                player['attack_type'] = "jump_attack"
                player['attack_timer'] = 30
                move_counts['jump_attack'] += 1
    
    screen.fill(GRAY)
    pygame.draw.rect(screen, WHITE, (0, FLOOR, WIDTH, HEIGHT-FLOOR))

    #Movement
    keys = pygame.key.get_pressed()
    if (keys[pygame.K_LEFT] and player['rect'].left > 0):
        player["rect"].x -= 5
    if (keys[pygame.K_RIGHT] and player['rect'].right < WIDTH):
        player["rect"].x += 5
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
    else:
        player['attacking'] = False
        player['attack_type'] = None
    if (player['parry_timer'] > 0):
        player['parry_timer'] -= 1
    else:
        player['parry_active'] = False
    if (boss['hit_cooldown'] > 0):
        boss['hit_cooldown'] -= 1

    if player['attacking'] and player['attack_type'] in ATTACK_DATA:
        attack = ATTACK_DATA[player['attack_type']]
        frames_elapsed = ({"light": 20, "heavy": 40, "jump_attack": 30}[player['attack_type']] )
    
    
    pygame.draw.rect(screen, player["color"], player["rect"])
    pygame.draw.rect(screen, boss['color'], boss['rect'])
    pygame.display.flip() #Displays everything written on screen
    clock.tick(FPS) #sets FPS cap so that time isn't faster based on processing power

print(move_counts)
pygame.quit()
sys.exit()