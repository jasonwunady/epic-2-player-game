import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants - 10x BIGGER GAME!
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
CANVAS_WIDTH = 680
CANVAS_HEIGHT = 800
LEVEL_HEIGHT = 20000  # MASSIVE 10x level!
GRAVITY = 0.5
JUMP_FORCE = -14
MOVE_SPEED = 6
PLAYER_SIZE = 60  # Collision box size
SPRITE_RENDER_SIZE = 360  # Visual sprite size (larger for better visibility)
BOUNCE_FORCE = -30  # Super bounce!
TRAP_DAMAGE = 25
PROJECTILE_SPEED = 10
ATTACK_COOLDOWN = 30  # Frames between attacks

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
# New special elements
BOUNCE_BLUE = (0, 191, 255)
TRAP_PURPLE = (148, 0, 211)
LAVA_RED = (255, 69, 0)

class Projectile:
    def __init__(self, x, y, direction, projectile_type, sprite, owner):
        self.x = x
        self.y = y
        self.direction = direction  # 1 for right, -1 for left
        self.type = projectile_type  # 'arrow' or 'axe'
        self.sprite = sprite
        self.width = 280 if projectile_type == 'arrow' else 420
        self.height = 280 if projectile_type == 'arrow' else 420
        self.active = True
        self.lifetime = 120  # Frames before disappearing
        self.owner = owner  # Which player shot this

    def update(self):
        self.x += PROJECTILE_SPEED * self.direction
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False

    def draw(self, surface, offset_x, camera_y):
        if not self.active:
            return
        screen_y = self.y - camera_y
        if self.sprite:
            sprite = self.sprite
            if self.direction < 0:
                sprite = pygame.transform.flip(sprite, True, False)
            surface.blit(sprite, (self.x + offset_x, screen_y))

class Player:
    def __init__(self, x, y, color, sprite_folder):
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
        self.sprite_folder = sprite_folder
        self.load_sprites()
        self.animation_frame = 0
        self.animation_timer = 0
        self.facing_right = True
        # Sprite offset to center larger sprite on smaller collision box
        # The sprite should be drawn so its bottom aligns with the collision box bottom
        self.sprite_offset_x = -(SPRITE_RENDER_SIZE - PLAYER_SIZE) // 2  # Center horizontally
        self.sprite_offset_y = -(SPRITE_RENDER_SIZE - PLAYER_SIZE - 10) // 2  # Align bottoms (sprite extends up)
        self.attack_cooldown = 0
        self.is_attacking = False
        self.attack_timer = 0

    def load_sprites(self):
        # Load sprite sheets
        try:
            idle_path = f'{self.sprite_folder}-Idle.png'
            walk_path = f'{self.sprite_folder}-Walk.png'
            hurt_path = f'{self.sprite_folder}-Hurt.png'

            print(f"Loading sprites from: {idle_path}")

            idle_sheet = pygame.image.load(idle_path)
            walk_sheet = pygame.image.load(walk_path)
            hurt_sheet = pygame.image.load(hurt_path)

            print(f"Idle sheet size: {idle_sheet.get_size()}")
            print(f"Walk sheet size: {walk_sheet.get_size()}")
            print(f"Hurt sheet size: {hurt_sheet.get_size()}")

            # Extract frames - each sheet has different frame counts
            # Idle: 6 frames, Walk: 8 frames, Hurt: 4 frames
            self.idle_frames = self.extract_frames(idle_sheet, 6, 100, 100)
            self.walk_frames = self.extract_frames(walk_sheet, 8, 100, 100)
            self.hurt_frames = self.extract_frames(hurt_sheet, 4, 100, 100)

            print(f"Extracted {len(self.idle_frames)} idle, {len(self.walk_frames)} walk, {len(self.hurt_frames)} hurt frames")

            # Scale to sprite render size (larger than collision box for better visibility)
            self.idle_frames = [pygame.transform.scale(f, (SPRITE_RENDER_SIZE, SPRITE_RENDER_SIZE)).convert_alpha() for f in self.idle_frames]
            self.walk_frames = [pygame.transform.scale(f, (SPRITE_RENDER_SIZE, SPRITE_RENDER_SIZE)).convert_alpha() for f in self.walk_frames]
            self.hurt_frames = [pygame.transform.scale(f, (SPRITE_RENDER_SIZE, SPRITE_RENDER_SIZE)).convert_alpha() for f in self.hurt_frames]

            print(f"Successfully loaded sprites!")
        except Exception as e:
            # Fallback to colored rectangles if sprites fail to load
            print(f"Failed to load sprites: {e}")
            import traceback
            traceback.print_exc()
            self.idle_frames = None
            self.walk_frames = None
            self.hurt_frames = None

    def extract_frames(self, sheet, frame_count, frame_width, frame_height):
        frames = []
        sheet_width, sheet_height = sheet.get_size()
        print(f"  Sheet dimensions: {sheet_width}x{sheet_height}")
        print(f"  Extracting {frame_count} frames of size {frame_width}x{frame_height}")

        for i in range(frame_count):
            x = i * frame_width
            rect = pygame.Rect(x, 0, frame_width, frame_height)
            print(f"  Frame {i}: x={x}, rect={rect}, valid={x + frame_width <= sheet_width and frame_height <= sheet_height}")

            if x + frame_width > sheet_width or frame_height > sheet_height:
                print(f"  ERROR: Frame {i} out of bounds!")
                raise ValueError(f"Frame {i} out of bounds: need {x + frame_width}x{frame_height}, have {sheet_width}x{sheet_height}")

            frame = sheet.subsurface(rect).copy()
            frames.append(frame)
        return frames

    def update(self, platforms):
        # Apply gravity
        self.vy += GRAVITY

        # Update position
        self.x += self.vx
        self.y += self.vy

        # Update animation
        self.animation_timer += 1
        if self.animation_timer >= 8:  # Change frame every 8 ticks
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 8  # Use max frame count

        # Update facing direction
        if self.vx > 0:
            self.facing_right = True
        elif self.vx < 0:
            self.facing_right = False

        # Update timers
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.respawning:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawning = False
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1
        else:
            self.is_attacking = False

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

    def jump(self, jump_sound=None):
        if self.on_ground:
            self.vy = JUMP_FORCE
            self.on_ground = False
            if jump_sound:
                jump_sound.play()

    def move_left(self):
        self.vx = -MOVE_SPEED

    def move_right(self):
        self.vx = MOVE_SPEED

    def attack(self, projectile_sprite, projectile_type):
        if self.attack_cooldown <= 0:
            self.attack_cooldown = ATTACK_COOLDOWN
            self.is_attacking = True
            self.attack_timer = 10
            # Create projectile in front of player
            direction = 1 if self.facing_right else -1
            proj_width = 280 if projectile_type == 'arrow' else 420
            proj_height = 280 if projectile_type == 'arrow' else 420

            # Position projectile centered on player
            if self.facing_right:
                proj_x = self.x + self.width
            else:
                proj_x = self.x - proj_width

            proj_y = self.y + (self.height // 2) - (proj_height // 2)
            return Projectile(proj_x, proj_y, direction, projectile_type, projectile_sprite, self)
        return None

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

        # Draw animated sprite if available
        if self.idle_frames and self.walk_frames and self.hurt_frames:
            # Choose animation based on state
            if self.invincible_timer > 0 and not self.respawning:
                frames = self.hurt_frames
            elif abs(self.vx) > 0:
                frames = self.walk_frames
            else:
                frames = self.idle_frames

            # Get current frame (wrap to available frames)
            frame_index = self.animation_frame % len(frames)
            current_frame = frames[frame_index]

            # Flip if facing left
            if not self.facing_right:
                current_frame = pygame.transform.flip(current_frame, True, False)

            # Draw sprite with offset to center it on collision box
            surface.blit(current_frame, (self.x + offset_x + self.sprite_offset_x, screen_y + self.sprite_offset_y))
        else:
            # Fallback to colored rectangle
            pygame.draw.rect(surface, self.color,
                            (self.x + offset_x, screen_y, self.width, self.height))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("2 Player Jump Game - 10x BIGGER!")
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

        # Load sound effects
        try:
            self.jump_sound = pygame.mixer.Sound('jump_sound_trimmed.wav')
            self.jump_sound.set_volume(0.8)
        except:
            self.jump_sound = None

        try:
            self.level_up_sound = pygame.mixer.Sound('pixel-level-up-sound-351836.mp3')
            self.level_up_sound.set_volume(0.4)
        except:
            self.level_up_sound = None

        try:
            self.winner_sound = pygame.mixer.Sound('winner-game-sound-404167.mp3')
            self.winner_sound.set_volume(0.6)
        except:
            self.winner_sound = None

        # Load projectile sprites
        try:
            arrow_img = pygame.image.load('Characters(100x100)/Soldier/Arrow(projectile)/Arrow01(100x100).png')
            self.arrow_sprite = pygame.transform.scale(arrow_img, (280, 280)).convert_alpha()
        except:
            self.arrow_sprite = None

        try:
            axe_img = pygame.image.load('Characters(100x100)/Orc/Orc(Split Effects)/Orc-attack01_Effect.png')
            self.axe_sprite = pygame.transform.scale(axe_img, (420, 420)).convert_alpha()
        except:
            self.axe_sprite = None

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

        # Generate massive level!
        seed = random.random()
        num_platforms = 200  # Lots of platforms!

        for i in range(num_platforms):
            x = 50 + ((seed + i * 0.3) % 1) * (CANVAS_WIDTH - 200)
            y = LEVEL_HEIGHT - 200 - (i * 95)  # Vertical spacing
            width = 80 + ((seed + i * 0.5) % 1) * 100

            # Variety of elements!
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
        # Gradient sky
        for y in range(CANVAS_HEIGHT):
            ratio = y / CANVAS_HEIGHT
            r = int(SKY_BLUE[0] + (CLOUD_WHITE[0] - SKY_BLUE[0]) * ratio)
            g = int(SKY_BLUE[1] + (CLOUD_WHITE[1] - SKY_BLUE[1]) * ratio)
            b = int(SKY_BLUE[2] + (CLOUD_WHITE[2] - SKY_BLUE[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (offset_x, y), (offset_x + CANVAS_WIDTH, y))

        # Moving clouds
        cloud_offset = int(camera_y * 0.2) % 150
        for i in range(10):
            cloud_x = offset_x + (i * 120 + cloud_offset) % CANVAS_WIDTH
            cloud_y = 50 + (i * 60) % 300
            # Cloud clusters
            for j in range(3):
                pygame.draw.circle(surface, CLOUD_WHITE, (cloud_x + j*15, cloud_y), 20 + j*5)

        # Mountains
        mountain_points = [(offset_x, CANVAS_HEIGHT)]
        for i in range(12):
            x = offset_x + (i * 60)
            y = 300 + (i % 4) * 80 + int(50 * math.sin(i * 0.5))
            mountain_points.append((x, y))
        mountain_points.append((offset_x + CANVAS_WIDTH, CANVAS_HEIGHT))
        pygame.draw.polygon(surface, MOUNTAIN_GRAY, mountain_points)

    def draw_level(self, surface, offset_x, camera_y):
        self.draw_background(surface, offset_x, camera_y)

        # Start line
        start_screen_y = LEVEL_HEIGHT - 40 - camera_y
        if start_screen_y >= -100 and start_screen_y <= CANVAS_HEIGHT + 100:
            pygame.draw.rect(surface, GREEN, (offset_x, start_screen_y, CANVAS_WIDTH, 40))
            start_text = self.small_font.render("START!", True, WHITE)
            surface.blit(start_text, (offset_x + 20, start_screen_y + 12))

        # Finish line - match the collision detection
        finish_screen_y = 760 - camera_y  # Match the y <= 800 check
        if finish_screen_y >= -100 and finish_screen_y <= CANVAS_HEIGHT + 100:
            pygame.draw.rect(surface, FINISH_RED, (offset_x, finish_screen_y, CANVAS_WIDTH, 40))
            finish_text = self.small_font.render("VICTORY!", True, WHITE)
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

        # Player 1 controls (Orc - WASD + S for attack)
        if keys[pygame.K_a]:
            self.player1.move_left()
        if keys[pygame.K_d]:
            self.player1.move_right()
        if keys[pygame.K_w]:
            self.player1.jump(self.jump_sound)
        if keys[pygame.K_s]:
            projectile = self.player1.attack(self.axe_sprite, 'axe')
            if projectile:
                self.projectiles.append(projectile)

        # Player 2 controls (Soldier - Arrows + Down for attack)
        if keys[pygame.K_LEFT]:
            self.player2.move_left()
        if keys[pygame.K_RIGHT]:
            self.player2.move_right()
        if keys[pygame.K_UP]:
            self.player2.jump(self.jump_sound)
        if keys[pygame.K_DOWN]:
            projectile = self.player2.attack(self.arrow_sprite, 'arrow')
            if projectile:
                self.projectiles.append(projectile)

    def update(self):
        if not self.game_won:
            self.update_music()
            self.update_platforms()

            if self.player1.update(self.platforms) and not self.game_won:
                self.game_won = True
                self.winner = 1
                if self.winner_sound:
                    self.winner_sound.play()

            if self.player2.update(self.platforms) and not self.game_won:
                self.game_won = True
                self.winner = 2
                if self.winner_sound:
                    self.winner_sound.play()

            # Update projectiles
            for projectile in self.projectiles[:]:
                projectile.update()
                if not projectile.active:
                    self.projectiles.remove(projectile)
                # Check collision with players (but not the owner)
                elif projectile.owner != self.player1 and (
                      projectile.x < self.player1.x + self.player1.width and
                      projectile.x + projectile.width > self.player1.x and
                      projectile.y < self.player1.y + self.player1.height and
                      projectile.y + projectile.height > self.player1.y):
                    self.player1.take_damage(10)
                    projectile.active = False
                elif projectile.owner != self.player2 and (
                      projectile.x < self.player2.x + self.player2.width and
                      projectile.x + projectile.width > self.player2.x and
                      projectile.y < self.player2.y + self.player2.height and
                      projectile.y + projectile.height > self.player2.y):
                    self.player2.take_damage(10)
                    projectile.active = False

    def draw(self):
        self.screen.fill(BLACK)

        # Draw game areas
        self.draw_level(self.screen, 10, self.player1.camera_y)
        self.player1.draw(self.screen, 10, self.player1.camera_y)
        self.player2.draw(self.screen, 10, self.player1.camera_y)
        # Draw projectiles for player 1's view
        for projectile in self.projectiles:
            projectile.draw(self.screen, 10, self.player1.camera_y)

        self.draw_level(self.screen, 710, self.player2.camera_y)
        self.player1.draw(self.screen, 710, self.player2.camera_y)
        self.player2.draw(self.screen, 710, self.player2.camera_y)
        # Draw projectiles for player 2's view
        for projectile in self.projectiles:
            projectile.draw(self.screen, 710, self.player2.camera_y)

        # Divider
        pygame.draw.line(self.screen, GOLD, (700, 0), (700, WINDOW_HEIGHT), 5)

        # UI
        title_text = self.font.render("10X MASSIVE LEVEL!", True, GOLD)
        self.screen.blit(title_text, (WINDOW_WIDTH // 2 - 150, 5))

        music_text = self.small_font.render("♪ Music Playing ♪", True, WHITE)
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

        # Status
        if self.game_won:
            if self.winner == 1:
                status1 = self.font.render("WINNER!", True, GOLD)
                status2 = self.font.render("Try again!", True, WHITE)
            else:
                status1 = self.font.render("Try again!", True, WHITE)
                status2 = self.font.render("WINNER!", True, GOLD)
        else:
            status1 = self.font.render("Climb!", True, WHITE)
            status2 = self.font.render("Climb!", True, WHITE)

        self.screen.blit(status1, (220, 860))
        self.screen.blit(status2, (920, 860))

        # Stats - fix height calculation to show 100% when winning
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

        # Reset button
        button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, 60, 200, 50)
        pygame.draw.rect(self.screen, BUTTON_GREEN, button_rect)
        button_text = self.font.render("New Game", True, WHITE)
        text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, text_rect)

        return button_rect

    def reset_game(self):
        self.game_won = False
        self.winner = None
        self.player1 = Player(100, LEVEL_HEIGHT - 150, RED, 'Characters(100x100)/Orc/Orc/Orc')
        self.player2 = Player(100, LEVEL_HEIGHT - 150, TEAL, 'Characters(100x100)/Soldier/Soldier/Soldier')
        self.platforms = self.generate_level()
        self.projectiles = []

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