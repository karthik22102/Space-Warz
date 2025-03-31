import pygame
from pygame import mixer
from random import randint, uniform

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load('assets/images/spaceship3.png').convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (80, 100))
        self.rect = self.image.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        self.direction = pygame.math.Vector2()
        self.speed = 300

        # cooldown
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
        if recent_keys[pygame.K_SPACE] and self.can_shoot:
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
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf 
        self.image = pygame.transform.smoothscale(meteor_surf, (90, 90))
        self.image = pygame.transform.rotate(self.image, randint(0, 360))
        self.rect = self.image.get_frect(center = pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 4000
        self.direction = pygame.math.Vector2(uniform(-0.5, 0.5), 1).normalize()
        self.speed = randint(400, 500)
        # self.angle = randint(0, 360)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill() 

def collisons():
    global running
    collison_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True)
    if collison_sprites:
        running = False

    for laser in laser_sprites:
        collied_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if collison_sprites:
            laser.kill()

#initialize the pygame
pygame.init()
# WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 680
# create the screen
info_object = pygame.display.Info()
WINDOW_WIDTH, WINDOW_HEIGHT = info_object.current_w, info_object.current_h
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.SCALED)
display_rect = display_surface.get_frect()
#Title and Icon
pygame.display.set_caption("Space Warz")
clock = pygame.time.Clock()



#importing image
display_background = pygame.image.load('assets/images/background5.jpg').convert_alpha()
display_background = pygame.transform.scale(display_background, (WINDOW_WIDTH, WINDOW_HEIGHT)) 

meteor_surf = pygame.image.load('assets/images/meteors/meteor 1.png').convert_alpha()
meteor_rect = meteor_surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))   

star_surf = pygame.image.load('assets/images/star1.png').convert_alpha()
star_positions = [(randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)) for i in range(20)]

laser_surf = pygame.image.load('assets/images/laser.png').convert_alpha()

# sprites
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
star_surf = pygame.image.load('assets/images/star1.png').convert_alpha()
for i in range(20):
    Star(all_sprites, star_surf)
player = Player(all_sprites)

# custom events
meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, 300)

# Starting the mixer 
mixer.init() 
  
# Loading the song 
mixer.music.load("assets/Sounds/MIDNIGHT HOURS.mp3") 
  
# Setting the volume 
# mixer.music.set_volume(0.7) 

# Load laser collision sound

  
# Start playing the song 
mixer.music.play() 

#Game Loop
running = True
while running:  
    dt = clock.tick() / 1000
    #event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == meteor_event:
            # x , y = randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)
            Meteor(meteor_surf, (randint(0, WINDOW_WIDTH), 0), (all_sprites, meteor_sprites))
            meteor_rect.x = randint(0, WINDOW_WIDTH)    
            meteor_rect.y = randint(0, WINDOW_HEIGHT)
            meteor_rect.clamp_ip(display_rect)
    #update
    all_sprites.update(dt)
    

    #draw the game
    display_surface.fill('darkgray')
    display_surface.blit(display_background, (0,0))
    # pygame.draw.rect(display_surface, 'red', laser_rect, width=2)

    all_sprites.draw(display_surface)

    collisons()

    pygame.display.update()

pygame.quit()