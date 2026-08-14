import random

class JumperBot:
    """Jumps constantly, occasionally jump-attacks, rarely does a normal attack. Should be countered by the boss"""

    name = "jumper"

    def choose_action(self, env):
        player = env.player

        if player['rect'].centerx < env.boss['rect'].centerx:
            toward = 'move_right'
        else:
            toward = 'move_left'

        #if airborne, sometimes throw out a jump attack
        if not player['onGround']:
            if random.random() < 0.05:
                return 'jump_attack'
            return 'nothing'
        
        #on the ground, jump most of the itmer
        if random.random() < 0.15:
            return 'jump'
        
        #sometimes throw a normal attack cause no player is only jumping
        if random.random() < 0.05:
            return 'light'
        
        #otherwise drift towards the boss
        return toward