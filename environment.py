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
        pass

    def calculate_reward(self):
        #score what just happened
        pass