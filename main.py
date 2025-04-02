import pygame
from pygame import mixer
from random import randint, uniform
import json
import os

# Initialize pygame
pygame.init()
info_object = pygame.display.Info()
WINDOW_WIDTH, WINDOW_HEIGHT = info_object.current_w, info_object.current_h
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.SCALED)
display_rect = display_surface.get_frect()
pygame.display.set_caption("Space Warz")
clock = pygame.time.Clock()

# Load assets
display_background = pygame.transform.scale(pygame.image.load('assets/images/Background4.jpg').convert_alpha(), 
                                          (WINDOW_WIDTH, WINDOW_HEIGHT))
menu_background = pygame.transform.scale(pygame.image.load('assets/images/MainMenu.jpg').convert_alpha(),
                                       (WINDOW_WIDTH, WINDOW_HEIGHT))
meteor_surf = pygame.image.load('assets/images/meteors/meteor 1.png').convert_alpha()
meteor_surf1 = pygame.image.load('assets/images/meteors/meteor 2.png').convert_alpha()
laser_surf = pygame.image.load('assets/images/laser.png').convert_alpha()
font_large = pygame.font.Font('assets/fonts/VCR_OSD_MONO.ttf', 80)
font_medium = pygame.font.Font('assets/fonts/VCR_OSD_MONO.ttf', 50)
font_small = pygame.font.Font('assets/fonts/VCR_OSD_MONO.ttf', 40)
font_tiny = pygame.font.Font('assets/fonts/VCR_OSD_MONO.ttf', 30)

# Game variables
score = 0
high_scores = []
difficulty_level = 0
difficulty_multiplier = 1
meteor_spawn_delay = 300
game_active = False
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

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load('assets/images/spaceship3.png').convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (70, 90))
        self.rect = self.image.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.direction = pygame.math.Vector2()
        self.speed = 300
        self.lives = 3
        self.can_shoot = True
        self.laser_shoot_time = 0
        self.cooldown_duration = 400

    def laser_timer(self):  
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True
    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction
        self.rect.clamp_ip(display_rect)
        self.rect.center += self.direction * self.speed * dt

        recent_keys = pygame.key.get_just_pressed()
        mouse_press = pygame.mouse.get_pressed()
        if (recent_keys[pygame.K_SPACE] or mouse_press[0]) and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()
        self.laser_timer()

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
    def __init__(self, surf, pos, groups, size_scale=1.0):
        super().__init__(groups)
        self.base_image = surf 
        self.size_scale = size_scale
        self.image = pygame.transform.smoothscale(self.base_image, 
                                                (int(70*size_scale), int(70*size_scale)))
        self.image = pygame.transform.rotate(self.image, randint(0, 360))
        self.rect = self.image.get_frect(center = pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 4000
        self.direction = pygame.math.Vector2(uniform(-0.5, 0.5), 1).normalize()  
        self.speed = randint(200, 300) 

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt * difficulty_multiplier
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
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

# Slider class (unchanged)
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

# Particle effect (unchanged)
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
volume_slider = Slider(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 50, 300, 20, 0, 1, volume)

# [Rest of your game classes (Player, Star, Laser, Meteor) remain unchanged...]

def collisions():
    global running, score, difficulty_multiplier, meteor_spawn_delay, difficulty_level, game_active
    hit_meteors = pygame.sprite.spritecollide(player, meteor_sprites, True)
    if hit_meteors:
        player.lives -= len(hit_meteors)
        if player.lives <= 0:
            game_active = False
            update_high_scores(score)
            reset_game()

    for laser in laser_sprites:
        hit_meteors = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if hit_meteors:
            score += len(hit_meteors)
            if score >= 10 and difficulty_level == 0:
                difficulty_level = 1
                difficulty_multiplier = 1.2
                meteor_spawn_delay = 500
                pygame.time.set_timer(meteor_event, meteor_spawn_delay)
            elif score >= 20 and difficulty_level == 1:
                difficulty_level = 2
                difficulty_multiplier = 1.5  # Keep same speed multiplier
                meteor_spawn_delay = 700  # Keep same spawn delay
                pygame.time.set_timer(meteor_event, meteor_spawn_delay)
            laser.kill()

def collisions1():
    global running, score, difficulty_multiplier, meteor_spawn_delay, difficulty_level, game_active
    hit_meteors1 = pygame.sprite.spritecollide(player, meteor_sprites1, True)
    if hit_meteors1:
        player.lives -= len(hit_meteors1)
        if player.lives <= 0:
            game_active = False
            update_high_scores(score)
            reset_game()
    for laser in laser_sprites:
        hit_meteors1 = pygame.sprite.spritecollide(laser, meteor_sprites1, True)
        if hit_meteors1:
            score += len(hit_meteors1) + 5
            laser.kill()
    

def update_high_scores(new_score):
    global high_scores
    high_scores.append(new_score)
    high_scores.sort(reverse=True)
    if len(high_scores) > 5:
        high_scores = high_scores[:5]
    save_high_scores()

def reset_game():
    global score, difficulty_level, difficulty_multiplier, meteor_spawn_delay
    score = 0
    difficulty_level = 0
    difficulty_multiplier = 1.0
    meteor_spawn_delay = 600
    pygame.time.set_timer(meteor_event, meteor_spawn_delay)
    
    for sprite in all_sprites:
        sprite.kill()
    
    for i in range(20):
        Star(all_sprites, pygame.image.load('assets/images/star1.png').convert_alpha())
    
    global player
    player = Player(all_sprites)

def display_score():
    score_text = font_medium.render(f"Score: {score}", True, (213, 217, 224))
    display_surface.blit(score_text, (10, 10))
    
    diff_color = (245, 152, 152)
    if player.lives == 2:
        diff_color = (242, 44, 44)
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
    display_surface.blit(vol_text, (WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 50))
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

# Initialize sprite groups and game objects
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
meteor_sprites1 = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()

for i in range(20):
    Star(all_sprites, pygame.image.load('assets/images/star1.png').convert_alpha())
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
        
        elif game_active and event.type == meteor_event:
            if difficulty_level == 2:  # Level 3 - larger meteors
                Meteor(meteor_surf, (randint(0, WINDOW_WIDTH), 0), 
                    (all_sprites, meteor_sprites), size_scale=1.2)
                Meteor(meteor_surf1, (randint(0, WINDOW_WIDTH), 0), 
                    (all_sprites, meteor_sprites1), size_scale=1.5)    # 1.5x size
            else:
                Meteor(meteor_surf, (randint(0, WINDOW_WIDTH), 0), 
                    (all_sprites, meteor_sprites))

    if game_active:
        all_sprites.update(dt)
        collisions()
        collisions1()

    display_surface.blit(display_background, (0,0))
    
    if game_active:
        all_sprites.draw(display_surface)
        display_score()
    elif in_settings:
        draw_settings()
    elif in_instructions:
        draw_instructions()
    else:
        draw_menu()
    
    pygame.display.update()

pygame.quit()