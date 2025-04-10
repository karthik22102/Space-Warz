import pygame
from pygame import mixer
from os.path import join
from random import randint, uniform
import json
import os
import math

# Initialize pygame
pygame.init()
info_object = pygame.display.Info()
WINDOW_WIDTH, WINDOW_HEIGHT = info_object.current_w, info_object.current_h
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.SCALED)
display_rect = display_surface.get_frect()
pygame.display.set_caption("Space Warz")
clock = pygame.time.Clock()

# Load assets
background_img = pygame.image.load(join('assets', 'images', 'Background4.png')).convert()
background_img = pygame.transform.scale(background_img, (WINDOW_WIDTH, WINDOW_HEIGHT))
background_img2 = background_img.copy()

lvl3_img = pygame.image.load(join('assets', 'images', 'Background5.png')).convert()
lvl3_img = pygame.transform.scale(lvl3_img, (WINDOW_WIDTH, WINDOW_HEIGHT))
lvl3_img2 = lvl3_img.copy()

menu_background = pygame.transform.scale(pygame.image.load(join('assets', 'images', 'MainMenu.jpg')).convert_alpha(),
                                       (WINDOW_WIDTH, WINDOW_HEIGHT))

meteor_surf = pygame.image.load(join('assets', 'images','meteors', 'meteor 1.png')).convert_alpha()
meteor_surf1 = pygame.image.load(join('assets', 'images','meteors', 'meteor 2.png')).convert_alpha()
meteor_surf2 = pygame.image.load(join('assets', 'images','meteors', 'meteor 3.png')).convert_alpha()
laser_surf = pygame.image.load(join('assets', 'images','Laser Sprites', '15.png')).convert_alpha()
laser_surf = pygame.transform.rotate(laser_surf, 90)
laser_surf = pygame.transform.smoothscale(laser_surf, (90, 90))
font_large = pygame.font.Font('assets/fonts/VCR_OSD_MONO.ttf', 80)
font_medium = pygame.font.Font('assets/fonts/VCR_OSD_MONO.ttf', 50)
font_small = pygame.font.Font('assets/fonts/VCR_OSD_MONO.ttf', 40)
font_tiny = pygame.font.Font('assets/fonts/VCR_OSD_MONO.ttf', 30)

# Scrolling variables
scroll_y = 0
scroll_speed = 100  # Pixels per second
current_background = background_img
current_background2 = background_img2

# Load Sound
laser_sound = mixer.Sound(join('assets/Sounds/laser.mp3'))
laser_sound.set_volume(0.1)
explosion_sound = mixer.Sound(join('assets/Sounds/explosion.wav'))
damage_sound = mixer.Sound(join('assets/Sounds/damage.ogg'))

# Load explosion frames
explosion_frames = [pygame.image.load(join('assets', 'images', 'explosion', f'{i}.png')).convert_alpha() for i in range(1, 10)]
explosion_frames1 = [pygame.image.load(join('assets', 'images', 'Pixel Art Explosions', 'PNG', 'Circle_explosion', f'{i}.png')).convert_alpha() for i in range(1, 10)]
explosion_frames2 = [pygame.image.load(join('assets', 'images', 'Pixel art', 'PNG_Animations', 'Shots', 'Shot6', f'{i}.png')).convert_alpha() for i in range(1, 10)]
explosion_frames2 = [pygame.transform.scale(frame, (int(frame.get_width() * 3), int(frame.get_height() * 3))) for frame in explosion_frames2]

boosts_frames = [pygame.image.load(join('assets', 'images', 'boost', f'{i}.png')).convert_alpha() for i in range(1, 10)]

# Game variables
score = 0
high_scores = []
difficulty_level = 0
difficulty_multiplier = 1
meteor_spawn_delay = 300
game_active = False
game_over = False
game_over_time = 0
in_settings = False
in_instructions = False
volume = 0.5
selected_difficulty = "Normal"
particles = []

# Load high scores
def load_high_scores():
    global high_scores
    try:
        if os.path.exists('high_scores.json'):
            with open('high_scores.json', 'r') as f:
                high_scores = json.load(f)
    except:
        high_scores = []

def save_high_scores():
    with open('high_scores.json', 'w') as f:
        json.dump(high_scores, f)

load_high_scores()

def lerp(a, b, t):
        """Linear interpolation between a and b by t"""
        return a + (b - a) * t

class AnimatedBoost(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(midtop=pos)  # Changed to midtop for better positioning
        self.active = True
        self.frame_speed = 20

    def update(self, dt):
        if self.active:
            self.frame_index += self.frame_speed * dt
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]
            # Maintain position relative to ship
            self.rect = self.image.get_frect(midtop=self.rect.midtop)

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        # Load ship image
        self.normal_image = pygame.image.load(join('assets', 'images', 'spaceship3.png')).convert_alpha()
        self.normal_image = pygame.transform.smoothscale(self.normal_image, (70, 90))
        self.image = self.normal_image
        self.rect = self.image.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        
        # Movement properties
        self.direction = pygame.math.Vector2()
        self.speed = 300
        self.boost_speed = 450
        self.lives = 3
        
        # Boost properties
        self.boost_particles = []
        self.boost_active = False
        self.idle_boost_active = True  # Always show some boost
        self.last_boost_time = 0
        self.boost_cooldown = 50  # ms between particle spawns
        self.idle_boost_cooldown = 100  # Slower for idle
        
        # Shooting properties
        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400
        
        # Mask for collision
        self.mask = pygame.mask.from_surface(self.image)

        # Boost animation with offset
        self.boost_offset = 30  # How many pixels below the ship the boost should appear
        boost_pos = (self.rect.centerx, self.rect.bottom + self.boost_offset)
        self.boost_animation = AnimatedBoost(boosts_frames, boost_pos, all_sprites)
        self.boost_intensity = 1  # 0-1 value for boost strength


    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction
        
                # Update boost animation position and intensity
        boost_pos = (self.rect.centerx, self.rect.bottom + self.boost_offset)
        self.boost_animation.rect.midbottom = boost_pos
        
        # Calculate boost intensity (1 when moving, 0.3 when idle)
        target_intensity = 1.0 if self.direction.length() > 0 else 0.3
        self.boost_intensity = lerp(self.boost_intensity, target_intensity, 0.1)  # Smooth transition
        
        # Control animation speed based on intensity
        self.boost_animation.frame_speed = 20 * self.boost_intensity
        
        # Make sure boost animation stays active
        self.boost_animation.active = True

        # Check if moving (boosting)
        self.boost_active = self.direction.length() > 0
        
        # Always show some boost (idle boost)
        current_time = pygame.time.get_ticks()
        cooldown = self.boost_cooldown if self.boost_active else self.idle_boost_cooldown
        
        if current_time - self.last_boost_time > cooldown:
            self.last_boost_time = current_time
            # Add new boost particles at ship's bottom center
            particle_count = 3 if self.boost_active else 1  # More particles when moving
            size_range = (3, 6) if self.boost_active else (2, 4)  # Larger when moving
            speed_range = (2, 4) if self.boost_active else (1, 2)  # Faster when moving
            
            for _ in range(particle_count):
                self.boost_particles.append({
                    'pos': [self.rect.midbottom[0] + uniform(-15, 15), self.rect.midbottom[1]],
                    'color': (randint(200, 255), randint(100, 200), randint(0, 100)),
                    'size': randint(*size_range),
                    'speed': uniform(*speed_range),
                    'life': randint(20, 40)
                })
        
        # Update existing particles
        for particle in self.boost_particles[:]:
            particle['pos'][1] += particle['speed']  # Move downward
            particle['size'] *= 0.98  # Shrink slightly
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.boost_particles.remove(particle)


        # Move with appropriate speed
        current_speed = self.boost_speed if self.boost_active else self.speed
        self.rect.clamp_ip(display_rect)
        self.rect.center += self.direction * current_speed * dt

        # Shooting logic
        recent_keys = pygame.key.get_just_pressed()
        mouse_press = pygame.mouse.get_pressed()
        if (recent_keys[pygame.K_SPACE] or mouse_press[0]) and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
            laser_sound.play()
        
        # Laser cooldown timer
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True
    
    def draw_boost(self, surface):
        # Draw boost particles with glow effect
        for particle in self.boost_particles:
            # Draw outer glow
            glow_surf = pygame.Surface((particle['size']*4, particle['size']*4), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf,
                (*particle['color'][:3], 50),  # Semi-transparent
                (particle['size']*2, particle['size']*2),
                particle['size']*2
            )
            surface.blit(glow_surf, (
                int(particle['pos'][0] - particle['size']*2),
                int(particle['pos'][1] - particle['size']*2)
            ))
            
            # Draw core particle
            pygame.draw.circle(
                surface,
                particle['color'],
                (int(particle['pos'][0]), int(particle['pos'][1])),
                int(particle['size'])
            )

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_frect(center = (randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)))
        self.rect.clamp_ip(self.rect)

class Laser(pygame.sprite.Sprite):
    def __init__(self,surf, pos, groups):
        super().__init__(groups)
        self.image = surf 
        self.rect = self.image.get_frect(midbottom = pos)
    
    def update(self, dt):
        self.rect.centery -= 1000 * dt
        if self.rect.bottom < 0:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups, size_scale=1.0, meteor_type=1):
        super().__init__(groups)
        self.base_image = surf 
        self.size_scale = size_scale
        self.meteor_type = meteor_type
        
        # Different properties based on meteor type
        if meteor_type == 2:  # Small meteor
            self.health = 2
            self.points = 5
            self.speed_range = (200, 300)
        elif meteor_type == 3:  # Special big meteor
            self.health = 3  # Takes 2 hits to destroy
            self.points = 20  # Worth more points
            self.speed_range = (150, 250)  # Slower
        else:
            self.health = 1
            self.points = 1 if meteor_type == 1 else 10
            self.speed_range = (200, 300)
            
        self.original_image = pygame.transform.smoothscale(self.base_image, 
            (int(70*size_scale), int(70*size_scale)))
        self.image = self.original_image
        self.rect = self.image.get_frect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 4000
        self.direction = pygame.math.Vector2(uniform(-0.5, 0.5), 1).normalize()  
        self.speed = randint(*self.speed_range)
        self.rotation = 0
        self.rotation_speed = uniform(-3, 3)
        
        # Add mask for better collision detection
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        # Update position based on direction and speed
        self.rect.center += self.direction * self.speed * dt
        
        # Rotate the meteor
        self.rotation += self.rotation_speed
        self.image = pygame.transform.rotate(self.original_image, self.rotation)
        self.rect = self.image.get_frect(center=self.rect.center)
        
        # Remove if off-screen or lifetime expired
        if (self.rect.top > WINDOW_HEIGHT or 
            self.rect.right < 0 or 
            self.rect.left > WINDOW_WIDTH or
            pygame.time.get_ticks() - self.start_time > self.lifetime):
            self.kill()

# Button class with transparent style
class Button:
    def __init__(self, x, y, width, height, text, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.text_color = text_color
        self.is_hovered = False
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def draw(self, surface):
        # Create transparent surface
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Draw button with different opacity based on hover state
        if self.is_hovered:
            pygame.draw.rect(button_surface, (*self.text_color, 50), (0, 0, self.rect.width, self.rect.height), 
                            border_radius=10)
            pygame.draw.rect(button_surface, (*self.text_color, 150), (0, 0, self.rect.width, self.rect.height), 
                            2, border_radius=10)
        else:
            pygame.draw.rect(button_surface, (*self.text_color, 30), (0, 0, self.rect.width, self.rect.height), 
                            border_radius=10)
            pygame.draw.rect(button_surface, (*self.text_color, 100), (0, 0, self.rect.width, self.rect.height), 
                            2, border_radius=10)
        
        surface.blit(button_surface, self.rect)
        
        # Draw text
        text_surf = font_small.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# Slider class
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_rect = pygame.Rect(x, y, 20, height + 10)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.dragging = False
        
    def draw(self, surface):
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        fill_width = int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, (0, 200, 0), fill_rect, border_radius=5)
        knob_x = self.rect.x + fill_width - 10
        self.knob_rect.x = max(self.rect.x - 10, min(knob_x, self.rect.right - 10))
        pygame.draw.rect(surface, (255, 255, 255), self.knob_rect, border_radius=5)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.knob_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value(event.pos[0])
            
    def update_value(self, mouse_x):
        mouse_x = max(self.rect.x, min(mouse_x, self.rect.right))
        self.val = self.min_val + (mouse_x - self.rect.x) / self.rect.width * (self.max_val - self.min_val)
        return self.val

# Particle effect
class Particle:
    def __init__(self):
        self.x = randint(0, WINDOW_WIDTH)
        self.y = randint(0, WINDOW_HEIGHT)
        self.size = randint(1, 3)
        self.speed = uniform(0.5, 1.5)
        self.color = (randint(200, 255), randint(200, 255), randint(200, 255))
        
    def update(self):
        self.y += self.speed
        if self.y > WINDOW_HEIGHT:
            self.y = 0
            self.x = randint(0, WINDOW_WIDTH)
            
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

# Create particles
for _ in range(100):
    particles.append(Particle())

# Create menu buttons with transparent style
play_button = Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 100, 300, 80, "PLAY", (255, 255, 255))
instructions_button = Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2, 300, 80, "INSTRUCTIONS", (255, 255, 255))
settings_button = Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 100, 300, 80, "SETTINGS", (255, 255, 255))
quit_button = Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 200, 300, 80, "QUIT", (255, 255, 255))

# Settings buttons
back_button = Button(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT - 100, 300, 80, "BACK", (255, 255, 255))
easy_button = Button(WINDOW_WIDTH//2 - 350, WINDOW_HEIGHT//2 - 50, 200, 60, "EASY", (0, 255, 0))
normal_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 50, 200, 60, "NORMAL", (255, 255, 0))
hard_button = Button(WINDOW_WIDTH//2 + 150, WINDOW_HEIGHT//2 - 50, 200, 60, "HARD", (255, 0, 0))

# Volume slider
volume_slider = Slider(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 130, 300, 20, 0, 1, volume)

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(center=pos)
        explosion_sound.play()
        explosion_sound.set_volume(0.05)

    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()

def update_background(dt):
    global scroll_y
    
    # Move the background upward
    scroll_y += scroll_speed * dt
    
    # Reset scroll when one full background has scrolled
    if scroll_y >= WINDOW_HEIGHT:
        scroll_y = 0

def collisions():
    global running, score, difficulty_multiplier, meteor_spawn_delay, difficulty_level, game_active, game_over, game_over_time
    global current_background, current_background2
    
    # Player collision with meteors
    hit_meteors = pygame.sprite.spritecollide(player, meteor_sprites, False, pygame.sprite.collide_mask)
    if hit_meteors:
        damage_sound.play()
        damage_sound.set_volume(0.2)
        for meteor in hit_meteors[:]:  # Iterate over a copy
            player.lives -= 1
            meteor.kill()
            if player.lives <= 0:
                game_over = True
                game_over_time = pygame.time.get_ticks()
                update_high_scores(score)
                break

    # Laser collision with meteors
    for laser in laser_sprites:
        hit_meteors = pygame.sprite.spritecollide(laser, meteor_sprites, False, pygame.sprite.collide_mask)
        if hit_meteors:
            for meteor in hit_meteors[:]:
                meteor.health -= 1
                if meteor.health <= 0:
                    score += meteor.points
                    meteor.kill()
                    # Different explosion for meteor type 3
                    if meteor.meteor_type == 3:
                        AnimatedExplosion(explosion_frames2, meteor.rect.center, all_sprites)
                    elif meteor.meteor_type == 2:
                        AnimatedExplosion(explosion_frames1, meteor.rect.center, all_sprites)
                    else:
                        AnimatedExplosion(explosion_frames, meteor.rect.center, all_sprites)
                    
                    # Difficulty progression
                    if score >= 10 and difficulty_level == 0:
                        difficulty_level = 1
                        difficulty_multiplier = 1.2
                        meteor_spawn_delay = 500
                    elif score >= 20 and difficulty_level == 1:
                        difficulty_level = 2
                        difficulty_multiplier = 1.5
                        meteor_spawn_delay = 700
                    elif score >= 100 and difficulty_level == 2:
                        difficulty_level = 3
                        difficulty_multiplier = 1.8
                        meteor_spawn_delay = 900
                        # Change background when reaching level 3
                        current_background = lvl3_img
                        current_background2 = lvl3_img2
                    
                    pygame.time.set_timer(meteor_event, meteor_spawn_delay)
                laser.kill()
                break

def update_high_scores(new_score):
    global high_scores
    high_scores.append(new_score)
    high_scores.sort(reverse=True)
    if len(high_scores) > 5:
        high_scores = high_scores[:5]
    save_high_scores()

def reset_game():
    global score, difficulty_level, difficulty_multiplier, meteor_spawn_delay, scroll_y
    global current_background, current_background2, game_over
    
    score = 0
    difficulty_level = 0
    difficulty_multiplier = 1.0
    meteor_spawn_delay = 600
    scroll_y = 0
    game_over = False
    current_background = background_img
    current_background2 = background_img2
    pygame.time.set_timer(meteor_event, meteor_spawn_delay)
    
    for sprite in all_sprites:
        sprite.kill()
    
    for i in range(20):
        Star(all_sprites, pygame.image.load(join('assets', 'images', 'star1.png')).convert_alpha())
    
    global player
    player = Player(all_sprites)

def display_score():
    score_text = font_medium.render(f"Score: {score}", True, (213, 217, 224))
    display_surface.blit(score_text, (10, 10))
    
    diff_color = (242, 242, 242)
    if player.lives == 2:
        diff_color = (247, 196, 10)
    elif player.lives == 1: 
        diff_color = (255, 28, 28)
    lives_text = font_medium.render(f"Lives: {player.lives}", True, diff_color)
    display_surface.blit(lives_text, (WINDOW_WIDTH - 300, 10))

def draw_menu():
    display_surface.blit(menu_background, (0, 0))
    for particle in particles:
        particle.update()
        particle.draw(display_surface)
    
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    display_surface.blit(overlay, (0, 0))
    
    for i in range(5, 0, -1):
        glow_color = (0, 255 // i, 255 // i)
        title_text = font_large.render("SPACE WARZ", True, glow_color)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//4))
        display_surface.blit(title_text, title_rect)
    
    play_button.draw(display_surface)
    instructions_button.draw(display_surface)
    settings_button.draw(display_surface)
    quit_button.draw(display_surface)
    
    hs_title = font_small.render("HIGH SCORES", True, (255, 255, 255))
    display_surface.blit(hs_title, (WINDOW_WIDTH - 250, 100))
    
    for i, hs in enumerate(high_scores[:5]):
        hs_text = font_tiny.render(f"{i+1}. {hs}", True, (255, 255, 255))
        display_surface.blit(hs_text, (WINDOW_WIDTH - 150, 150 + i * 40))

def draw_settings():
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    display_surface.blit(overlay, (0, 0))
    
    title_text = font_large.render("SETTINGS", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, 100))
    display_surface.blit(title_text, title_rect)
    
    vol_text = font_medium.render("VOLUME", True, (255, 255, 255))
    display_surface.blit(vol_text, (WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 40))
    volume_slider.draw(display_surface)
    vol_value = font_small.render(f"{int(volume*100)}%", True, (255, 255, 255))
    display_surface.blit(vol_value, (WINDOW_WIDTH//2 + 170, WINDOW_HEIGHT//2 + 40))
    
    diff_text = font_medium.render("DIFFICULTY", True, (255, 255, 255))
    display_surface.blit(diff_text, (WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 150))
    
    easy_button.draw(display_surface)
    normal_button.draw(display_surface)
    hard_button.draw(display_surface)
    
    current_time = pygame.time.get_ticks()
    pulse = abs(int((current_time % 1000) / 1000 * 100 - 50)) + 50
    
    if selected_difficulty == "Easy":
        pygame.draw.rect(display_surface, (0, 255, 0, pulse), easy_button.rect, 3, border_radius=10)
    elif selected_difficulty == "Normal":
        pygame.draw.rect(display_surface, (255, 255, 0, pulse), normal_button.rect, 3, border_radius=10)
    elif selected_difficulty == "Hard":
        pygame.draw.rect(display_surface, (255, 0, 0, pulse), hard_button.rect, 3, border_radius=10)
    
    back_button.draw(display_surface)

def draw_instructions():
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    display_surface.blit(overlay, (0, 0))
    
    title_text = font_large.render("INSTRUCTIONS", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, 100))
    display_surface.blit(title_text, title_rect)
    
    instructions = [
        "HOW TO PLAY:",
        "",
        "- Use WASD or Arrow Keys to move your ship",
        "- Press SPACE or Left Click to shoot lasers",
        "- Destroy meteors to earn points",
        "- Avoid getting hit by meteors",
        "- You have 3 lives",
        "",
        "DIFFICULTY:",
        "",
        "- Game gets harder as you score more points",
        "- Select difficulty in Settings",
        "",
        "Press ESC or BACK to return to menu"
    ]
    
    for i, line in enumerate(instructions):
        if line.startswith("-"):
            text = font_tiny.render(line, True, (200, 200, 200))
        elif line == "HOW TO PLAY:" or line == "DIFFICULTY:":
            text = font_small.render(line, True, (100, 255, 255))
        else:
            text = font_tiny.render(line, True, (255, 255, 255))
        
        display_surface.blit(text, (WINDOW_WIDTH//2 - 300, 200 + i * 30))
    
    back_button.draw(display_surface)

def draw_game_over():
        # Draw all meteors falling behind the overlay for visual effect
    all_sprites.draw(display_surface)
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    display_surface.blit(overlay, (0, 0))
    
    # Game Over text with pulsing effect
    current_time = pygame.time.get_ticks()
    pulse = abs(math.sin(current_time / 500)) * 255
    game_over_text = font_large.render("GAME OVER", True, (255, pulse, pulse))
    game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3))
    display_surface.blit(game_over_text, game_over_rect)
    
    # Final score
    score_text = font_medium.render(f"Final Score: {score}", True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
    display_surface.blit(score_text, score_rect)
    
    # High score if applicable
    if high_scores and score == high_scores[0]:
        hs_text = font_small.render("NEW HIGH SCORE!", True, (255, 255, 0))
        hs_rect = hs_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 60))
        display_surface.blit(hs_text, hs_rect)
    
    # Continue prompt
    continue_text = font_small.render("Press any key to continue", True, (200, 200, 200))
    continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 100))
    display_surface.blit(continue_text, continue_rect)
    


# Initialize sprite groups and game objects
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
meteor_sprites1 = pygame.sprite.Group()
meteor_sprites2 = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()

for i in range(20):
    Star(all_sprites, pygame.image.load(join('assets', 'images', 'star1.png')).convert_alpha())
player = Player(all_sprites)

meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, meteor_spawn_delay)

mixer.init() 
mixer.music.load("assets/Sounds/MIDNIGHT HOURS.mp3") 
mixer.music.set_volume(volume)
mixer.music.play(-1)

# Main game loop
running = True
while running:  
    dt = clock.tick(60) / 1000
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if not game_active:
            if in_settings:
                volume_slider.handle_event(event)
                volume = volume_slider.val
                mixer.music.set_volume(volume)
                
                if back_button.is_clicked(mouse_pos, event):
                    in_settings = False
                elif easy_button.is_clicked(mouse_pos, event):
                    selected_difficulty = "Easy"
                    difficulty_multiplier = 0.8
                elif normal_button.is_clicked(mouse_pos, event):
                    selected_difficulty = "Normal"
                    difficulty_multiplier = 1.0
                elif hard_button.is_clicked(mouse_pos, event):
                    selected_difficulty = "Hard"
                    difficulty_multiplier = 1.2
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        in_settings = False
            
            elif in_instructions:
                if back_button.is_clicked(mouse_pos, event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    in_instructions = False
            
            else:
                play_button.check_hover(mouse_pos)
                instructions_button.check_hover(mouse_pos)
                settings_button.check_hover(mouse_pos)
                quit_button.check_hover(mouse_pos)
                
                if play_button.is_clicked(mouse_pos, event):
                    game_active = True
                    reset_game()
                if instructions_button.is_clicked(mouse_pos, event):
                    in_instructions = True
                if settings_button.is_clicked(mouse_pos, event):
                    in_settings = True
                if quit_button.is_clicked(mouse_pos, event):
                    running = False
        
        elif game_active and not game_over and event.type == meteor_event:
            if difficulty_level >= 2:  # Level 3+
                # Spawn regular meteors (small chance)
                if randint(1, 100) <= 70:
                    Meteor(meteor_surf, (randint(0, WINDOW_WIDTH), 0), 
                        (all_sprites, meteor_sprites), size_scale=1.0, meteor_type=1)
                
                # Spawn medium meteors
                Meteor(meteor_surf1, (randint(0, WINDOW_WIDTH), 0), 
                    (all_sprites, meteor_sprites), size_scale=1.5, meteor_type=2)
                
                # Spawn big meteors (less frequent)
                if difficulty_level >= 3 and randint(1, 100) <= 30:
                    Meteor(meteor_surf2, (randint(0, WINDOW_WIDTH), 0), 
                        (all_sprites, meteor_sprites), size_scale=2.0, meteor_type=3)
            else:
                # Normal meteor spawning for levels 1-2
                Meteor(meteor_surf, (randint(0, WINDOW_WIDTH), 0), 
                    (all_sprites, meteor_sprites), size_scale=1.0, meteor_type=1)
    
    # Draw everything
    if game_active:
        if game_over:
            # Wait a moment before showing game over screen
            if pygame.time.get_ticks() - game_over_time > 1000:
                draw_game_over()
                # Check for any key press to return to menu
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                        game_active = False
                        game_over = False
                        reset_game()
        else:
            update_background(dt)
            all_sprites.update(dt)
            collisions()
            
            # Draw the scrolling background - ensure perfect alignment
            display_surface.blit(current_background, (0, scroll_y))
            display_surface.blit(current_background2, (0, scroll_y - WINDOW_HEIGHT))
            
            all_sprites.draw(display_surface)
            player.draw_boost(display_surface)
            display_score()
    elif in_settings:
        draw_settings()
    elif in_instructions:
        draw_instructions()
    else:
        draw_menu()
    
    pygame.display.update()

pygame.quit()