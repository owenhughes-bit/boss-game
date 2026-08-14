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
SLAM_REACH_UP = 60
SLAM_REACH_FORWARD = 70

PLAYER_MOVE_SPEED = 5
PLAYER_MOVE_SPEED_ATTACKING = 1.3
JUMP_VELOCITY = -12

DAMAGE_DEALT_WEIGHT = 1.0
DAMAGE_TAKEN_WEIGHT = 1.0
TIME_PENALTY = 0.01
WIN_REWARD = 100.0
LOSS_PENALTY = 100.0

recovery_map = {"light": 8, "heavy": 18, "jump_attack": 10}

ATTACK_DATA = {
    "light": {"damage": 10, "width": 40, "height": 20, "active_frames": (5, 15)},
    "heavy": {"damage": 25, "width": 60, "height": 30, "active_frames": (10, 35)},
    "jump_attack": {"damage": 15, "width": 50, "height": 25, "active_frames": (5, 20)},
}
ATTACK_DURATION = {"light": 20, "heavy": 40, "jump_attack": 30}

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
STATE_SIZE = 8

class BossFightEnv:
    def __init__(self, render=False, opponent_bot = None):
        self.render = render
        self.opponent_bot = opponent_bot
        if self.render:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        #build fresh player and boss state, return opening state
        player_start_x = random.randint(150, 300)
        boss_start_x = player_start_x + random.randint(200, 350)

        self.player = {
            "rect": pygame.Rect(player_start_x, 300, 50, 80),
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
            "rect": pygame.Rect(boss_start_x, FLOOR - 90, 60, 90),
            "hp": 200,
            "max_hp": 200,
            "hit_cooldown": 0,
            "state": 'idle',
            "state_timer": 90,
            "attack_type": None,
            "facing": 'left',
            'vel_x': 0,
        }
        self.prev_player_hp = self.player['hp']
        self.prev_boss_hp = self.boss['hp']
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
        if self.player['invincible_timer'] > 0:
            self.player['invincible_timer'] -= 1
        
        if self.opponent_bot is not None:
            player_action = self.opponent_bot.choose_action(self)
            self.apply_player_action(player_action)

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
            if distance < BOSS_RETREAT_DISTANCE:
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
            if self.boss['rect'].right > WIDTH:
                self.boss['rect'].right = WIDTH
            
            #layer 3
            # build the boss's hitbox for this attack
            if self.boss['facing'] == 'left':
                boss_hitbox = pygame.Rect(
                    self.boss['rect'].left - attack['width'],
                    self.boss['rect'].y + 10,
                    attack['width'],
                    attack['height'],
                )
            else:
                boss_hitbox = pygame.Rect(
                    self.boss['rect'].right,
                    self.boss['rect'].y + 10,
                    attack['width'],
                    attack['height'],
                )

            # spin hits both sides
            if self.boss['attack_type'] == 'spin':
                boss_hitbox = pygame.Rect(
                    self.boss['rect'].left - attack['width'],
                    self.boss['rect'].y + 10,
                    attack['width'] * 2 + self.boss['rect'].width,
                    attack['height'],
                )

            # slam is the anti-air uppercut
            if self.boss['attack_type'] == 'slam':
                if self.boss['facing'] == 'right':
                    boss_hitbox = pygame.Rect(
                        self.boss['rect'].right - 20,
                        self.boss['rect'].top - SLAM_REACH_UP,
                        SLAM_REACH_FORWARD,
                        SLAM_REACH_UP + 40,
                    )
                else:
                    boss_hitbox = pygame.Rect(
                        self.boss['rect'].left + 20 - SLAM_REACH_FORWARD,
                        self.boss['rect'].top - SLAM_REACH_UP,
                        SLAM_REACH_FORWARD,
                        SLAM_REACH_UP + 40,
                    )

            # does it connect?
            if boss_hitbox.colliderect(self.player['rect']) and self.player['invincible_timer'] == 0:
                if self.player['parry_active'] and not self.player['parry_used']:
                    self.player['parry_used'] = True
                    if self.player['parry_timer'] > 22:
                        # perfect parry: boss is stunned
                        self.boss['state'] = 'stunned'
                        self.boss['state_timer'] = 90
                        self.boss['vel_x'] = 0
                elif not self.player['parry_active']:
                    self.player['hp'] -= attack['damage']
                    self.player['invincible_timer'] = 40
                    self.player['vel_x'] = -8 if self.boss['facing'] == 'left' else 8
                    self.player['vel_y'] = -5

            self.boss['state_timer'] -= 1
            if self.boss['state_timer'] <= 0:
                self.boss['vel_x'] = 0
                self.boss['state'] = 'recovery'
                self.boss['state_timer'] = attack['recovery']

        elif self.boss['state'] == 'stunned':
            self.boss['vel_x'] = 0
            self.boss['state_timer'] -= 1
            if self.boss['state_timer'] <= 0:
                self.boss['state'] = 'idle'
        
        # --- player's attack hits the boss ---
        if self.player['attacking'] and self.player['attack_type'] in ATTACK_DATA:
            p_attack = ATTACK_DATA[self.player['attack_type']]
            total_frames = ATTACK_DURATION[self.player['attack_type']]
            frames_elapsed = total_frames - self.player['attack_timer']
            active_start, active_end = p_attack['active_frames']

            if active_start <= frames_elapsed <= active_end:
                if self.player['facing'] == 'right':
                    hitbox = pygame.Rect(
                        self.player['rect'].right,
                        self.player['rect'].y + 10,
                        p_attack['width'],
                        p_attack['height'],
                    )
                else:
                    hitbox = pygame.Rect(
                        self.player['rect'].left - p_attack['width'],
                        self.player['rect'].y + 10,
                        p_attack['width'],
                        p_attack['height'],
                    )

                if hitbox.colliderect(self.boss['rect']) and self.boss['hit_cooldown'] == 0:
                    self.boss['hp'] -= p_attack['damage']
                    self.boss['hit_cooldown'] = total_frames
                    self.player['attack_landed'] = True

        # --- done check + return ---
        done = self.player['hp'] <= 0 or self.boss['hp'] <= 0
        reward = self.calculate_reward()
        return self.get_state(), reward, done
    
    def apply_player_action(self, action):
        p = self.player

        if action == 'move_left':
            if not p['attacking'] and p['recovery_timer'] == 0:
                p['facing'] = 'left'
            p['rect'].x -= PLAYER_MOVE_SPEED_ATTACKING if (p['attacking'] or p['recovery_timer'] > 0) else PLAYER_MOVE_SPEED

        elif action == 'move_right':
            if not p['attacking'] and p['recovery_timer'] == 0:
                p['facing'] = 'right'
            p['rect'].x += PLAYER_MOVE_SPEED_ATTACKING if (p['attacking'] or p['recovery_timer'] > 0) else PLAYER_MOVE_SPEED

        elif action == 'jump':
            if p['onGround']:
                p['vel_y'] = JUMP_VELOCITY

        elif action == 'light':
            if not p['attacking'] and p['onGround'] and not p['parry_active'] and p['recovery_timer'] == 0:
                p['attacking'] = True
                p['attack_type'] = 'light'
                p['attack_timer'] = ATTACK_DURATION['light']
                p['attack_landed'] = False

        elif action == 'heavy':
            if not p['attacking'] and p['onGround'] and not p['parry_active'] and p['recovery_timer'] == 0:
                p['attacking'] = True
                p['attack_type'] = 'heavy'
                p['attack_timer'] = ATTACK_DURATION['heavy']
                p['attack_landed'] = False

        elif action == 'jump_attack':
            if not p['onGround'] and not p['attacking'] and not p['parry_active'] and p['recovery_timer'] == 0:
                p['attacking'] = True
                p['attack_type'] = 'jump_attack'
                p['attack_timer'] = ATTACK_DURATION['jump_attack']
                p['attack_landed'] = False

        elif action == 'parry':
            if not p['attacking'] and p['parry_recovery_timer'] == 0:
                p['parry_active'] = True
                p['parry_timer'] = 30
                p['parry_used'] = False

        # 'nothing' → do nothing


    def calculate_reward(self):
        reward = 0.0

        #damage delt to the player - good
        damage_dealt = self.prev_player_hp - self.player['hp']
        reward += damage_dealt * DAMAGE_DEALT_WEIGHT

        #damage delt to the boss - bad
        damage_taken = self.prev_boss_hp - self.boss['hp']
        reward -= damage_taken * DAMAGE_TAKEN_WEIGHT

        reward -= TIME_PENALTY

        if self.player['hp'] <= 0:
            reward += WIN_REWARD
        if self.boss['hp'] <= 0:
            reward -= LOSS_PENALTY

        self.prev_player_hp = self.player['hp']
        self.prev_boss_hp = self.boss['hp']

        return reward

