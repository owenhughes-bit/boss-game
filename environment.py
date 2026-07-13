import pygame
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
WHIFF_MULTIPLIER = 2.5

recovery_map = {"light": 8, "heavy": 18, "jump_attack": 10}

BOSS_ATTACKS = {
    "slash": {"damage": 15, "width": 70, "height": 30, "windup": 40, "active": 15, "recovery": 30},
    "lunge": {"damage": 25, "width": 70, "height": 40, "windup": 60, "active": 20, "recovery": 45},
    "jab": {"damage": 10, "width": 50, "height": 25, "windup": 20, "active": 10, "recovery": 20},
    "slam": {"damage": 20, "width": 80, "height": 50, "windup": 50, "active": 20, "recovery": 40},
    "spin": {"damage": 18, "width": 70, "height": 35, "windup": 45, "active": 25, "recovery": 35},
    "feint": {"damage": 0, "width": 0, "height": 0, "windup": 35, "active": 1, "recovery": 25},
}

ACTION_MAP = {
    0: 'idle',
    1: 'jab',
    2: 'slash',
    3: 'lunge',
    4: 'slam',
    5: 'spin',
    6: 'feint',
}
ACTION_SIZE = len(ACTION_MAP)

class BossFightEnv:
    def __init__(self, render=False):
        self.render = render
        if self.render:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        #build fresh player and boss state, return opening state
        self.player = {
            "rect": pygame.Rect(150, 300, 50, 80),
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
            "parry_recovery_timer": 0,
            "attack_landed": False,
            "recovery_timer": 0,
        }

        self.boss = {
            "rect": pygame.Rect(600, FLOOR - 90, 60, 90),
            "hp": 200,
            "max_hp": 200,
            "hit_cooldown": 0,
            "state": 'idle',
            "state_timer": 90,
            "attack_type": None,
            "facing": 'left',
            'vel_x': 0,
        }
        return self.get_state()

    def get_state(self):
        #turn the current situation into a list of numbers for the network
        horizontalDistance = abs(self.boss['rect'].centerx - self.player['rect'].centerx) / WIDTH
        bossHp = self.boss['hp'] / self.boss['max_hp']
        playerHp = self.player['hp'] / self.player['max_hp']
        playerAttacking = int(self.player['attacking'])
        playerAirborne = int(not(self.player['onGround']))
        playerParrying = int(self.player['parry_active'])
        playerRecovery = int(self.player['recovery_timer'] > 0)
        playerParryRecovery = int(self.player['parry_recovery_timer'] > 0)

        # Style Vector Appended Here Later

        return [
            horizontalDistance,
            bossHp,
            playerHp,
            playerAttacking,
            playerAirborne,
            playerParrying,
            playerRecovery,
            playerParryRecovery,
        ]

    def step(self, action):
        #apply the boss' action, advance one frame, return (state, reward, done)
        self.player['vel_y'] += GRAVITY
        self.player['rect'].y += self.player['vel_y']
        if (self.player['rect'].bottom >= FLOOR):
            self.player['rect'].bottom = FLOOR
            self.player['vel_y'] = 0
            self.player['onGround'] = True
        else:
            self.player['onGround'] = False
        
        #Fighting
        if (self.player['attack_timer'] > 0):
            self.player['attack_timer'] -= 1
        if self.player['attack_timer'] == 0 and self.player['attacking']:
            base_recovery = recovery_map.get(self.player['attack_type'], 8)
            if not self.player['attack_landed']:
                base_recovery = int(base_recovery * WHIFF_MULTIPLIER)
            self.player['recovery_timer'] = base_recovery
            self.player['attacking'] = False
            self.player['attack_type'] = None
        if self.player['recovery_timer'] > 0:
            self.player['recovery_timer'] -= 1
        if (self.player['parry_timer'] > 0):
            self.player['parry_timer'] -= 1
        else:
            if self.player['parry_active']:
                if not self.player['parry_used']:
                    self.player['parry_recovery_timer'] = 25
                    print("Parry whiffed!")
                self.player['parry_active'] = False
                self.player['parry_used'] = False
        if self.player['parry_recovery_timer'] > 0:
            self.player['parry_recovery_timer'] -= 1
        if (self.boss['hit_cooldown'] > 0):
            self.boss['hit_cooldown'] -= 1
        if (self.boss['vel_x'] > 0):
            self.boss['vel_x'] -= 0.5
        elif (self.boss['vel_x'] < 0):
            self.boss['vel_x'] += 0.5
        self.player['rect'].x += self.player['vel_x']
        if self.player['vel_x'] > 0:
            self.player['vel_x'] -= 0.8
        elif self.player['vel_x'] < 0:
            self.player['vel_x'] += 0.8
        if abs(self.player['vel_x']) < 0.8:
            self.player['vel_x'] = 0
        if self.player['rect'].left < 0:
            self.player['rect'].left = 0
        if self.player['rect'].right > WIDTH:
            self.player['rect'].right = WIDTH
        
        #player_action = self.opponent_bot.choose_action(self)

        #-- Layer 2: Boss --
        if self.boss['state'] == 'idle':
            if self.player['rect'].centerx < self.boss['rect'].centerx:
                self.boss['facing'] = 'left'
            else:
                self.boss['facing'] = 'right'

            #scripted movement
            distance = abs(self.player['rect'].centerx - self.boss['rect'].centerx)
            if distance > BOSS_CHASE_DISTANCE:
                if (self.boss['facing'] == 'left'):
                    self.boss['rect'].x -= BOSS_WALK_SPEED
                else:
                    self.boss['rect'].x += BOSS_WALK_SPEED
            if distance < BOSS_CHASE_DISTANCE:
                if (self.boss['facing'] == 'left'):
                    self.boss['rect'].x += BOSS_RETREAT_SPEED
                else:
                    self.boss['rect'].x -= BOSS_RETREAT_SPEED

            if self.boss['rect'].left < 0:
                self.boss['rect'].left = 0
            if self.boss['rect'].right > WIDTH:
                self.boss['rect'].right = WIDTH

            move = ACTION_MAP[action]
            if move != 'idle':
                self.boss['attack_type'] = move
                self.boss['state'] = 'windup'
                self.boss['state_timer'] = BOSS_ATTACKS[move]['windup']
            #Windup
            elif self.boss['state'] == 'windup':
                self.boss['state_timer'] -= 1
                if self.boss['state_timer'] <= 0:
                    self.boss['state'] = 'active'
                    self.boss['state_timer'] = BOSS_ATTACKS[self.boss['attack_type']]['active']
            #Recovery
            elif self.boss['state'] == 'recovery':
                self.boss['state_timer'] -= 1
                if self.boss['state_timer'] <= 0:
                    self.boss['state'] = 'idle'

        elif self.boss['state'] == 'active':
            attack = BOSS_ATTACKS[self.boss['attack_type']]

            #lunge
            if self.boss['attack_type'] == 'lunge':
                self.boss['vel_x'] = -8 if self.boss['facing'] == 'left' else 8
            else:
                self.boss['vel_x'] = 0
            self.boss['rect'].x += self.boss['vel_x']

            #clamp to screen
            if self.boss['rect'].left < 0:
                self.boss['rect'].left = 0
            if self.boss['rect'].right > 0:
                self.boss['rect'].right = WIDTH
            
            #layer 3

            self.boss['state_timer'] -= 1
            if self.boss['state_timer'] <= 0:
                self.boss['vel_x'] = 0
                self.boss['state'] = 'recovery'
                self.boss['state_timer'] = attack['recovery']



    def calculate_reward(self):
        #score what just happened
        pass