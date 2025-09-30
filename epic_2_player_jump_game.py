import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants - 10x EPIC GAME!
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
CANVAS_WIDTH = 680
CANVAS_HEIGHT = 800
LEVEL_HEIGHT = 20000  # MASSIVE 10x level!
GRAVITY = 0.5
JUMP_FORCE = -14
MOVE_SPEED = 6
PLAYER_SIZE = 30
BOUNCE_FORCE = -30  # Super bounce!
TRAP_DAMAGE = 25

# Colors
SKY_BLUE = (135, 206, 235)
CLOUD_WHITE = (248, 248, 255)
MOUNTAIN_GRAY = (169, 169, 169)
RED = (255, 107, 107)
TEAL = (78, 205, 196)
GREEN = (0, 255, 0)
FINISH_RED = (255, 0, 0)
BROWN = (139, 69, 19)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (85, 85, 85)
GOLD = (255, 215, 0)
BUTTON_GREEN = (76, 175, 80)
CRACKED_BROWN = (101, 50, 13)
ORANGE = (255, 165, 0)
# New epic elements
BOUNCE_BLUE = (0, 191, 255)
TRAP_PURPLE = (148, 0, 211)
LAVA_RED = (255, 69, 0)

class Player:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.vx = 0
        self.vy = 0
        self.color = color
        self.on_ground = False
        self.finished = False
        self.camera_y = 0
        self.highest_y = y
        self.respawn_timer = 0
        self.respawning = False
        self.health = 100
        self.invincible_timer = 0

    def update(self, platforms):
        # Apply gravity
        self.vy += GRAVITY

        # Update position
        self.x += self.vx
        self.y += self.vy

        # Update timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.respawning:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawning = False

        # Reset ground state
        self.on_ground = False

        # Check platform collisions
        for platform in platforms:
            if (self.x < platform['x'] + platform['width'] and
                self.x + self.width > platform['x'] and
                self.y < platform['y'] + platform['height'] and
                self.y + self.height > platform['y']):

                if platform['state'] == 'broken':
                    continue

                # Landing on top
                if self.vy > 0 and self.y < platform['y']:
                    self.y = platform['y'] - self.height
                    self.vy = 0
                    self.on_ground = True
                    platform['players_on'].add(self)

                    # Handle special platform types
                    if platform['type'] == 'bounce':
                        self.vy = BOUNCE_FORCE  # Super bounce!
                        self.on_ground = False
                    elif platform['type'] == 'trap' and self.invincible_timer <= 0:
                        self.take_damage(TRAP_DAMAGE)
                    elif platform['type'] == 'lava' and self.invincible_timer <= 0:
                        self.take_damage(TRAP_DAMAGE * 2)  # Lava hurts more!

                    # Start cracking normal platforms
                    if platform['state'] == 'normal' and platform['type'] == 'normal':
                        platform['state'] = 'cracking'
                        platform['crack_timer'] = 120

                # Other collisions
                elif self.vy < 0 and self.y > platform['y']:
                    self.y = platform['y'] + platform['height']
                    self.vy = 0
                elif self.vx > 0:
                    self.x = platform['x'] - self.width
                elif self.vx < 0:
                    self.x = platform['x'] + platform['width']

        # Ground collision
        if self.y + self.height > LEVEL_HEIGHT - 40:
            self.y = LEVEL_HEIGHT - 40 - self.height
            self.vy = 0
            self.on_ground = True

        # Wall collision
        if self.x < 0:
            self.x = 0
        if self.x + self.width > CANVAS_WIDTH:
            self.x = CANVAS_WIDTH - self.width

        # Update camera
        target_camera_y = self.y - CANVAS_HEIGHT + 200
        if target_camera_y < 0:
            target_camera_y = 0
        if target_camera_y > LEVEL_HEIGHT - CANVAS_HEIGHT:
            target_camera_y = LEVEL_HEIGHT - CANVAS_HEIGHT
        self.camera_y = target_camera_y

        # Track highest point
        if self.y < self.highest_y:
            self.highest_y = self.y

        # Check for fatal fall
        fall_distance = self.y - self.highest_y
        if fall_distance > 1000 and not self.respawning:
            self.respawn_closer()
            return False

        # Check health
        if self.health <= 0 and not self.respawning:
            self.respawn_closer()
            return False

        # Check finish line - make it easier to reach and more accurate
        if self.y <= 800 and not self.finished:  # Lower finish line for better gameplay
            self.finished = True
            return True

        self.vx = 0
        return False

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_FORCE
            self.on_ground = False

    def move_left(self):
        self.vx = -MOVE_SPEED

    def move_right(self):
        self.vx = MOVE_SPEED

    def take_damage(self, damage):
        if self.invincible_timer <= 0:
            self.health -= damage
            self.invincible_timer = 60
            return True
        return False

    def respawn_closer(self):
        respawn_y = self.highest_y + 500
        if respawn_y >= LEVEL_HEIGHT - 200:
            respawn_y = LEVEL_HEIGHT - 150

        self.x = CANVAS_WIDTH // 2
        self.y = respawn_y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.respawning = True
        self.respawn_timer = 60
        self.health = 100
        self.invincible_timer = 120
        self.finished = False

    def draw(self, surface, offset_x, camera_y):
        screen_y = self.y - camera_y

        # Flash when respawning or taking damage
        if (self.respawning and (self.respawn_timer // 10) % 2) or (self.invincible_timer > 0 and (self.invincible_timer // 5) % 2):
            return

        pygame.draw.rect(surface, self.color,
                        (self.x + offset_x, screen_y, self.width, self.height))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("EPIC 2 Player Jump Game - 10x BIGGER!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.reset_game()
        self.setup_music()

    def setup_music(self):
        # Load and play background music
        try:
            pygame.mixer.music.load('somersaults-edm-ost-track-176960.mp3')
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # Loop indefinitely
        except:
            print("Could not load background music")

    def update_music(self):
        # Music is handled by pygame.mixer.music
        pass

    def generate_level(self):
        platforms = []

        # Ground
        platforms.append({
            'x': 0,
            'y': LEVEL_HEIGHT - 40,
            'width': CANVAS_WIDTH,
            'height': 40,
            'state': 'solid',
            'type': 'normal',
            'crack_timer': 0,
            'players_on': set()
        })

        # Generate EPIC MASSIVE level!
        seed = random.random()
        num_platforms = 200  # EPIC number of platforms!

        for i in range(num_platforms):
            x = 50 + ((seed + i * 0.3) % 1) * (CANVAS_WIDTH - 200)
            y = LEVEL_HEIGHT - 200 - (i * 95)  # Epic vertical spacing
            width = 80 + ((seed + i * 0.5) % 1) * 100

            # Epic variety of elements!
            element_type = 'normal'
            if i % 6 == 0 and i > 0:  # Bounce pads
                element_type = 'bounce'
                width = 60
            elif i % 10 == 0 and i > 5:  # Spike traps
                element_type = 'trap'
                width = 40
            elif i % 15 == 0 and i > 10:  # Lava traps
                element_type = 'lava'
                width = 70

            platforms.append({
                'x': x,
                'y': y,
                'width': width,
                'height': 25,
                'state': 'normal',
                'type': element_type,
                'crack_timer': 0,
                'players_on': set()
            })

        return platforms

    def update_platforms(self):
        for platform in self.platforms:
            platform['players_on'].clear()

            for player in [self.player1, self.player2]:
                if (player.x < platform['x'] + platform['width'] and
                    player.x + player.width > platform['x'] and
                    player.y + player.height >= platform['y'] and
                    player.y + player.height <= platform['y'] + platform['height'] + 10):
                    platform['players_on'].add(player)

            if platform['state'] == 'cracking':
                platform['crack_timer'] -= 1
                if platform['crack_timer'] <= 0:
                    platform['state'] = 'broken'
                elif platform['crack_timer'] <= 30:
                    platform['state'] = 'about_to_break'

    def draw_background(self, surface, offset_x, camera_y):
        # Epic gradient sky
        for y in range(CANVAS_HEIGHT):
            ratio = y / CANVAS_HEIGHT
            r = int(SKY_BLUE[0] + (CLOUD_WHITE[0] - SKY_BLUE[0]) * ratio)
            g = int(SKY_BLUE[1] + (CLOUD_WHITE[1] - SKY_BLUE[1]) * ratio)
            b = int(SKY_BLUE[2] + (CLOUD_WHITE[2] - SKY_BLUE[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (offset_x, y), (offset_x + CANVAS_WIDTH, y))

        # Epic moving clouds
        cloud_offset = int(camera_y * 0.2) % 150
        for i in range(10):
            cloud_x = offset_x + (i * 120 + cloud_offset) % CANVAS_WIDTH
            cloud_y = 50 + (i * 60) % 300
            # Epic cloud clusters
            for j in range(3):
                pygame.draw.circle(surface, CLOUD_WHITE, (cloud_x + j*15, cloud_y), 20 + j*5)

        # Epic mountains
        mountain_points = [(offset_x, CANVAS_HEIGHT)]
        for i in range(12):
            x = offset_x + (i * 60)
            y = 300 + (i % 4) * 80 + int(50 * math.sin(i * 0.5))
            mountain_points.append((x, y))
        mountain_points.append((offset_x + CANVAS_WIDTH, CANVAS_HEIGHT))
        pygame.draw.polygon(surface, MOUNTAIN_GRAY, mountain_points)

    def draw_level(self, surface, offset_x, camera_y):
        self.draw_background(surface, offset_x, camera_y)

        # Epic start line
        start_screen_y = LEVEL_HEIGHT - 40 - camera_y
        if start_screen_y >= -100 and start_screen_y <= CANVAS_HEIGHT + 100:
            pygame.draw.rect(surface, GREEN, (offset_x, start_screen_y, CANVAS_WIDTH, 40))
            start_text = self.small_font.render("EPIC START!", True, WHITE)
            surface.blit(start_text, (offset_x + 20, start_screen_y + 12))

        # Epic finish line - match the collision detection
        finish_screen_y = 760 - camera_y  # Match the y <= 800 check
        if finish_screen_y >= -100 and finish_screen_y <= CANVAS_HEIGHT + 100:
            pygame.draw.rect(surface, FINISH_RED, (offset_x, finish_screen_y, CANVAS_WIDTH, 40))
            finish_text = self.small_font.render("EPIC VICTORY!", True, WHITE)
            surface.blit(finish_text, (offset_x + 20, finish_screen_y + 12))

        # Draw all platforms and special elements
        for platform in self.platforms:
            screen_y = platform['y'] - camera_y
            if screen_y >= -100 and screen_y <= CANVAS_HEIGHT + 100:

                # Choose color based on type and state
                if platform['type'] == 'bounce':
                    color = BOUNCE_BLUE
                elif platform['type'] == 'trap':
                    color = TRAP_PURPLE
                elif platform['type'] == 'lava':
                    color = LAVA_RED
                elif platform['state'] == 'cracking':
                    color = CRACKED_BROWN
                elif platform['state'] == 'about_to_break':
                    color = ORANGE if (platform['crack_timer'] // 5) % 2 else CRACKED_BROWN
                elif platform['state'] == 'broken':
                    continue
                else:
                    color = BROWN

                pygame.draw.rect(surface, color,
                               (platform['x'] + offset_x, screen_y,
                                platform['width'], platform['height']))

                # Special effects
                if platform['type'] == 'bounce':
                    # Bounce pad indicator
                    pygame.draw.circle(surface, WHITE,
                                     (platform['x'] + offset_x + platform['width']//2,
                                      screen_y + platform['height']//2), 8)
                    bounce_text = self.small_font.render("↑", True, WHITE)
                    surface.blit(bounce_text, (platform['x'] + offset_x + platform['width']//2 - 5,
                                              screen_y + platform['height']//2 - 8))

                elif platform['type'] == 'trap':
                    # Spike indicators
                    for spike in range(0, platform['width'], 10):
                        spike_x = platform['x'] + offset_x + spike
                        pygame.draw.polygon(surface, WHITE,
                                          [(spike_x, screen_y),
                                           (spike_x + 5, screen_y - 8),
                                           (spike_x + 10, screen_y)])

                elif platform['type'] == 'lava':
                    # Lava bubbles
                    for bubble in range(0, platform['width'], 15):
                        bubble_x = platform['x'] + offset_x + bubble + 7
                        pygame.draw.circle(surface, ORANGE,
                                         (bubble_x, screen_y + 5), 3)

                # Crack effects for normal platforms
                if platform['state'] in ['cracking', 'about_to_break'] and platform['type'] == 'normal':
                    mid_x = platform['x'] + offset_x + platform['width'] // 2
                    mid_y = screen_y + platform['height'] // 2
                    pygame.draw.line(surface, BLACK,
                                   (mid_x, screen_y),
                                   (mid_x, screen_y + platform['height']), 2)
                    pygame.draw.line(surface, BLACK,
                                   (platform['x'] + offset_x, mid_y),
                                   (platform['x'] + offset_x + platform['width'], mid_y), 2)

    def handle_input(self, keys):
        if self.game_won:
            return

        # Player 1 controls
        if keys[pygame.K_a]:
            self.player1.move_left()
        if keys[pygame.K_d]:
            self.player1.move_right()
        if keys[pygame.K_w]:
            self.player1.jump()

        # Player 2 controls
        if keys[pygame.K_LEFT]:
            self.player2.move_left()
        if keys[pygame.K_RIGHT]:
            self.player2.move_right()
        if keys[pygame.K_UP]:
            self.player2.jump()

    def update(self):
        if not self.game_won:
            self.update_music()
            self.update_platforms()

            if self.player1.update(self.platforms) and not self.game_won:
                self.game_won = True
                self.winner = 1

            if self.player2.update(self.platforms) and not self.game_won:
                self.game_won = True
                self.winner = 2

    def draw(self):
        self.screen.fill(BLACK)

        # Draw epic game areas
        self.draw_level(self.screen, 10, self.player1.camera_y)
        self.player1.draw(self.screen, 10, self.player1.camera_y)
        self.player2.draw(self.screen, 10, self.player1.camera_y)

        self.draw_level(self.screen, 710, self.player2.camera_y)
        self.player1.draw(self.screen, 710, self.player2.camera_y)
        self.player2.draw(self.screen, 710, self.player2.camera_y)

        # Epic divider
        pygame.draw.line(self.screen, GOLD, (700, 0), (700, WINDOW_HEIGHT), 5)

        # Epic UI
        title_text = self.font.render("EPIC 10X MASSIVE LEVEL!", True, GOLD)
        self.screen.blit(title_text, (WINDOW_WIDTH // 2 - 150, 5))

        music_text = self.small_font.render("♪ Epic Music Playing ♪", True, WHITE)
        self.screen.blit(music_text, (WINDOW_WIDTH // 2 - 80, 35))

        # Player info
        player1_label = self.font.render("Player 1", True, RED)
        player2_label = self.font.render("Player 2", True, TEAL)
        self.screen.blit(player1_label, (250, 810))
        self.screen.blit(player2_label, (950, 810))

        controls1 = self.small_font.render("WASD", True, WHITE)
        controls2 = self.small_font.render("Arrows", True, WHITE)
        self.screen.blit(controls1, (260, 835))
        self.screen.blit(controls2, (960, 835))

        # Epic status
        if self.game_won:
            if self.winner == 1:
                status1 = self.font.render("EPIC WINNER!", True, GOLD)
                status2 = self.font.render("Try again!", True, WHITE)
            else:
                status1 = self.font.render("Try again!", True, WHITE)
                status2 = self.font.render("EPIC WINNER!", True, GOLD)
        else:
            status1 = self.font.render("Epic Climb!", True, WHITE)
            status2 = self.font.render("Epic Climb!", True, WHITE)

        self.screen.blit(status1, (220, 860))
        self.screen.blit(status2, (920, 860))

        # Epic stats - fix height calculation to show 100% when winning
        # Calculate height based on actual finish line position
        finish_y = 800  # Match finish line position
        height1 = max(0, min(100, int((LEVEL_HEIGHT - self.player1.y) / (LEVEL_HEIGHT - finish_y) * 100)))
        height2 = max(0, min(100, int((LEVEL_HEIGHT - self.player2.y) / (LEVEL_HEIGHT - finish_y) * 100)))

        # Show 100% if player finished
        if self.player1.finished:
            height1 = 100
        if self.player2.finished:
            height2 = 100

        height_text1 = self.small_font.render(f"Height: {height1}%", True, WHITE)
        height_text2 = self.small_font.render(f"Height: {height2}%", True, WHITE)
        self.screen.blit(height_text1, (230, 885))
        self.screen.blit(height_text2, (930, 885))

        health_color1 = GREEN if self.player1.health > 50 else ORANGE if self.player1.health > 25 else RED
        health_color2 = GREEN if self.player2.health > 50 else ORANGE if self.player2.health > 25 else RED

        health_text1 = self.small_font.render(f"Health: {self.player1.health}", True, health_color1)
        health_text2 = self.small_font.render(f"Health: {self.player2.health}", True, health_color2)
        self.screen.blit(health_text1, (350, 885))
        self.screen.blit(health_text2, (1050, 885))

        # Epic reset button
        button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, 60, 200, 50)
        pygame.draw.rect(self.screen, BUTTON_GREEN, button_rect)
        button_text = self.font.render("New Epic Game", True, WHITE)
        text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, text_rect)

        return button_rect

    def reset_game(self):
        self.game_won = False
        self.winner = None
        self.player1 = Player(100, LEVEL_HEIGHT - 150, RED)
        self.player2 = Player(100, LEVEL_HEIGHT - 150, TEAL)
        self.platforms = self.generate_level()

    def run(self):
        running = True

        while running:
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        button_rect = self.draw()
                        if button_rect.collidepoint(event.pos):
                            self.reset_game()

            self.handle_input(keys)
            self.update()
            button_rect = self.draw()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()