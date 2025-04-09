import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Playable Area
PLAYABLE_WIDTH = 680
ROAD_LEFT_BOUNDARY = (SCREEN_WIDTH - PLAYABLE_WIDTH) // 2
ROAD_RIGHT_BOUNDARY = ROAD_LEFT_BOUNDARY + PLAYABLE_WIDTH

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0) # For ammo text

# Game states
START, PLAYING, GAME_OVER = 0, 1, 2

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cognizant Game")

# --- Asset Loading ---
try:
    print("Loading assets...")
    bike_image = pygame.image.load('bike.png').convert_alpha()
    obstacle_image = pygame.image.load('obstacle.png').convert_alpha()
    boost_image = pygame.image.load('boost.png').convert_alpha()
    road_image = pygame.image.load('road.png').convert()
    ammo_image = pygame.image.load('ammo.png').convert_alpha() # <-- NEW: Load ammo image

    # Load Individual Explosion Images
    explosion_files = [
        'explosion1.png', 'explosion2.png', 'explosion3.png',
        'explosion4.png', 'explosion5.png'
    ]
    explosion_anim = []
    EXPLOSION_SCALE_FACTOR = 1.0

    print("Loading explosion frames...")
    for filename in explosion_files:
        try:
            frame = pygame.image.load(filename).convert_alpha()
            if EXPLOSION_SCALE_FACTOR != 1.0:
                original_width = frame.get_width()
                original_height = frame.get_height()
                new_width = int(original_width * EXPLOSION_SCALE_FACTOR)
                new_height = int(original_height * EXPLOSION_SCALE_FACTOR)
                frame = pygame.transform.scale(frame, (new_width, new_height))
            explosion_anim.append(frame)
            print(f" - Loaded {filename}")
        except pygame.error as e:
            print(f"Error loading explosion frame '{filename}': {e}")

    if not explosion_anim:
         print("WARNING: No explosion animation frames loaded!")
         # Add a placeholder if needed, or handle appropriately
         placeholder_surf = pygame.Surface((1, 1))
         placeholder_surf.set_alpha(0) # Invisible placeholder
         explosion_anim.append(placeholder_surf)


except pygame.error as e:
    print(f"Error loading assets: {e}")
    print("Ensure 'bike.png', 'obstacle.png', 'boost.png', 'road.png', 'ammo.png', and")
    print("the explosion image files ('explosion1.png' to 'explosion5.png') are present.")
    pygame.quit()
    exit()
print("Asset loading complete.")


# Scale images
bike_image = pygame.transform.scale(bike_image, (75, 150))
obstacle_image = pygame.transform.scale(obstacle_image, (50, 50))
boost_image = pygame.transform.scale(boost_image, (50, 50))
ammo_image = pygame.transform.scale(ammo_image, (40, 40)) # <-- NEW: Scale ammo image
road_image = pygame.transform.scale(road_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# --- Sound Loading ---
try:
    print("Loading sounds...")
    laser_sound = pygame.mixer.Sound('laser.wav')
    explosion_sound = pygame.mixer.Sound('explosion.wav')
    boost_sound = pygame.mixer.Sound('boost.wav')
    # Optional: Add a distinct sound for ammo pickup
    ammo_pickup_sound = pygame.mixer.Sound('ammo_pickup.mp3') # Reusing boost sound for now
except pygame.error as e:
    print(f"Error loading sound: {e}")
    # Sounds are optional, continue without them
    laser_sound = None
    explosion_sound = None
    boost_sound = None
    ammo_pickup_sound = None
print("Sound loading complete.")


# Function to safely play sounds
def play_sound(sound):
    if sound:
        sound.play()

# --- Sprite Classes ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = bike_image
        self.rect = self.image.get_rect()
        self.starting_ammo = 10 # <-- NEW: Define starting ammo
        self.reset() # Call reset to initialize position and ammo

    def update(self):
        keys = pygame.key.get_pressed()
        current_speed = self.speed * 1.5 if self.boosted else self.speed
        if keys[pygame.K_LEFT] and self.rect.left > ROAD_LEFT_BOUNDARY:
            self.rect.x -= current_speed
        if keys[pygame.K_RIGHT] and self.rect.right < ROAD_RIGHT_BOUNDARY:
            self.rect.x += current_speed
        # Clamp position
        if self.rect.left < ROAD_LEFT_BOUNDARY:
            self.rect.left = ROAD_LEFT_BOUNDARY
        if self.rect.right > ROAD_RIGHT_BOUNDARY:
            self.rect.right = ROAD_RIGHT_BOUNDARY

    def shoot(self):
        # --- MODIFIED: Check and use ammo ---
        if self.ammo > 0:
            self.ammo -= 1 # Use one ammo
            laser = Laser(self.rect.centerx, self.rect.top)
            all_sprites.add(laser)
            lasers.add(laser)
            play_sound(laser_sound)
        # else:
            # Optional: Play an 'empty' sound effect here
            # print("Out of ammo!") # Debug message
        # --- End Modification ---

    def add_ammo(self, amount):
        # --- NEW: Method to add ammo ---
        self.ammo += amount
        # print(f"Ammo picked up! Current ammo: {self.ammo}") # Debug message

    def reset(self):
        # --- MODIFIED: Reset ammo as well ---
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.speed = 5
        self.boosted = False
        self.boost_timer = 0
        self.ammo = self.starting_ammo # Reset to starting ammo
        # --- End Modification ---


class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = obstacle_image
        self.rect = self.image.get_rect()
        self.reset_position()
        self.base_speed = 5
        self.speed = self.base_speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.reset_position()

    def reset_position(self):
        max_left_x = ROAD_RIGHT_BOUNDARY - self.rect.width
        upper_bound = max(ROAD_LEFT_BOUNDARY, max_left_x)
        try:
            self.rect.x = random.randint(ROAD_LEFT_BOUNDARY, upper_bound)
        except ValueError:
             self.rect.x = ROAD_LEFT_BOUNDARY # Fallback
        self.rect.y = random.randint(-SCREEN_HEIGHT, -self.rect.height)

    def set_speed(self, new_speed):
        self.speed = new_speed

    def reset_speed(self):
        self.speed = self.base_speed

class Boost(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = boost_image
        self.rect = self.image.get_rect()
        self.reset_position()
        self.base_speed = 5 # Boost items fall slightly faster maybe?
        self.speed = self.base_speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
             self.reset_position()

    def reset_position(self):
        max_left_x = ROAD_RIGHT_BOUNDARY - self.rect.width
        upper_bound = max(ROAD_LEFT_BOUNDARY, max_left_x)
        try:
            self.rect.x = random.randint(ROAD_LEFT_BOUNDARY, upper_bound)
        except ValueError:
             self.rect.x = ROAD_LEFT_BOUNDARY # Fallback
        self.rect.y = random.randint(-SCREEN_HEIGHT * 2, -self.rect.height * 2) # Spawn further up

    def set_speed(self, new_speed):
        self.speed = new_speed

    def reset_speed(self):
        self.speed = self.base_speed


# --- NEW: AmmoPack Class ---
class AmmoPack(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = ammo_image
        self.rect = self.image.get_rect()
        self.reset_position()
        self.base_speed = 6 # Ammo falls a bit faster?
        self.speed = self.base_speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
             self.reset_position() # Respawn when it goes off screen

    def reset_position(self):
        # Spawn within the playable road area
        max_left_x = ROAD_RIGHT_BOUNDARY - self.rect.width
        upper_bound = max(ROAD_LEFT_BOUNDARY, max_left_x)
        try:
            self.rect.x = random.randint(ROAD_LEFT_BOUNDARY, upper_bound)
        except ValueError:
             self.rect.x = ROAD_LEFT_BOUNDARY # Fallback

        # Spawn randomly off-screen (top)
        self.rect.y = random.randint(-SCREEN_HEIGHT * 3, -self.rect.height * 2) # Spawn further up

    def set_speed(self, new_speed):
        self.speed = new_speed

    def reset_speed(self):
        self.speed = self.base_speed
# --- End AmmoPack Class ---


class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.speed = -12 # Faster laser

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, animation_frames):
        super().__init__()
        self.animation_frames = animation_frames
        if not self.animation_frames:
             self.kill(); return
        self.image = self.animation_frames[0]
        self.rect = self.image.get_rect(center=center)
        self.frame_index = 0
        self.last_update_time = pygame.time.get_ticks()
        self.frame_rate_ms = 60 # Animation speed

    def update(self):
        if not hasattr(self, 'animation_frames') or not self.animation_frames:
            self.kill(); return
        now = pygame.time.get_ticks()
        if now - self.last_update_time > self.frame_rate_ms:
            self.last_update_time = now
            self.frame_index += 1
            if self.frame_index >= len(self.animation_frames):
                self.kill()
            else:
                center = self.rect.center
                self.image = self.animation_frames[self.frame_index]
                self.rect = self.image.get_rect(center=center)


# --- Game Setup ---
player = Player()
obstacles = pygame.sprite.Group()
boosts = pygame.sprite.Group()
lasers = pygame.sprite.Group()
ammo_packs = pygame.sprite.Group() # <-- NEW: Ammo pack group
all_sprites = pygame.sprite.Group()

all_sprites.add(player)

# --- Function to populate initial sprites ---
def populate_initial_sprites():
    print("Populating initial sprites...")
    for _ in range(5): # Initial obstacles
        obstacle = Obstacle(); obstacles.add(obstacle); all_sprites.add(obstacle)
    for _ in range(1): # Initial boosts
        boost = Boost(); boosts.add(boost); all_sprites.add(boost)
    for _ in range(2): # <-- NEW: Initial ammo packs
        ammo_pack = AmmoPack(); ammo_packs.add(ammo_pack); all_sprites.add(ammo_pack)
    print("Initial sprites populated.")

populate_initial_sprites() # Call it once at the start

score = 0
font = pygame.font.Font(None, 36)
# Smaller font for controls text
small_font = pygame.font.Font(None, 24)

background_y = 0
base_background_speed = 5
background_speed = base_background_speed

# Game control text lines
controls_text_lines = [
    "Controls:",
    "Left/Right Arrows: Move",
    "F: Shoot",
]
start_controls_text_lines = [
    "Controls:",
    "Left/Right Arrows: Move",
    "F: Shoot",
]
game_over_controls_text_lines = [
     "Controls:",
     "R: Restart",
]


running = True
clock = pygame.time.Clock()
game_state = START
boost_duration = 180
boost_speed_multiplier = 2
ammo_per_pack = 5 # <-- NEW: How much ammo a pack gives

# --- Function to draw multiline text ---
def draw_text_lines(surface, text_lines, font_to_use, color, bottomright_pos):
    line_height = font_to_use.get_height() + 3 # Add spacing
    current_y = bottomright_pos[1] # Start Y from the bottom
    for line in reversed(text_lines): # Draw from bottom line upwards
        text_surface = font_to_use.render(line, True, color)
        text_rect = text_surface.get_rect()
        text_rect.bottomright = (bottomright_pos[0], current_y)
        surface.blit(text_surface, text_rect)
        current_y -= line_height # Move Y up for the next line

# --- Game Loop ---
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_state == START:
                if event.key == pygame.K_SPACE:
                    game_state = PLAYING
            elif game_state == PLAYING:
                 if event.key == pygame.K_f:
                    player.shoot() # Shoot logic now uses ammo
            elif game_state == GAME_OVER:
                if event.key == pygame.K_r:
                    print("Resetting game...")
                    game_state = START # Go to start screen after reset
                    score = 0
                    player.reset() # Resets position AND ammo
                    background_speed = base_background_speed
                    background_y = 0
                    # Clear all non-player sprites
                    for sprite in all_sprites:
                         if sprite != player:
                             sprite.kill()
                    # Repopulate all items
                    populate_initial_sprites()


    # --- Game State Logic ---
    if game_state == PLAYING:
        all_sprites.update() # Update all sprites

        # Boost handling
        if player.boosted:
            player.boost_timer -= 1
            if player.boost_timer <= 0:
                player.boosted = False
                background_speed = base_background_speed
                # Reset speeds of falling items
                for group in [obstacles, boosts, ammo_packs]:
                    for item in group:
                        item.reset_speed()

        # --- Collision Checks ---
        # Player vs Obstacles
        if pygame.sprite.spritecollideany(player, obstacles):
            play_sound(explosion_sound)
            game_state = GAME_OVER

        # Player vs Boosts
        collected_boosts = pygame.sprite.spritecollide(player, boosts, True) # Kill boost on collect
        if collected_boosts:
            player.boosted = True; player.boost_timer = boost_duration; play_sound(boost_sound)
            boosted_speed = base_background_speed * boost_speed_multiplier; background_speed = boosted_speed
            # Speed up existing items
            for group in [obstacles, boosts, ammo_packs]:
                for item in group:
                    item.set_speed(item.base_speed * boost_speed_multiplier)
            # Respawn a boost
            new_boost = Boost()
            if player.boosted: new_boost.set_speed(new_boost.base_speed * boost_speed_multiplier)
            boosts.add(new_boost); all_sprites.add(new_boost)

        # --- NEW: Player vs AmmoPacks ---
        collected_ammo = pygame.sprite.spritecollide(player, ammo_packs, True) # Kill pack on collect
        if collected_ammo:
            player.add_ammo(ammo_per_pack)
            play_sound(ammo_pickup_sound) # Play ammo pickup sound
            # Respawn an ammo pack
            new_ammo = AmmoPack()
            # Ensure its speed matches current game speed (boosted or not)
            if player.boosted:
                new_ammo.set_speed(new_ammo.base_speed * boost_speed_multiplier)
            ammo_packs.add(new_ammo)
            all_sprites.add(new_ammo)
        # --- End AmmoPack Collision ---

        # Lasers vs Obstacles
        hits = pygame.sprite.groupcollide(lasers, obstacles, False, False)
        for laser, hit_obstacles_list in hits.items():
            laser.kill()
            for obstacle in hit_obstacles_list:
                if obstacle.alive(): # Check if obstacle wasn't already hit this frame
                    score += 10
                    play_sound(explosion_sound)
                    explosion = Explosion(obstacle.rect.center, explosion_anim)
                    all_sprites.add(explosion)
                    obstacle.kill()
                    # Respawn obstacle
                    new_obstacle = Obstacle()
                    if player.boosted: new_obstacle.set_speed(new_obstacle.base_speed * boost_speed_multiplier)
                    obstacles.add(new_obstacle); all_sprites.add(new_obstacle)

        # Score update & Background scroll
        score += 1 # Simple time/distance score
        background_y += background_speed
        if background_y >= SCREEN_HEIGHT: background_y = 0

        # --- Draw ---
        # Background
        screen.blit(road_image, (0, background_y))
        screen.blit(road_image, (0, background_y - SCREEN_HEIGHT))
        # Sprites
        all_sprites.draw(screen)
        # Score (Top Left)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # --- NEW: Ammo Count (Bottom Left) ---
        ammo_text_surface = font.render(f"Ammo: {player.ammo}", True, YELLOW) # Yellow color
        ammo_text_rect = ammo_text_surface.get_rect()
        ammo_text_rect.bottomleft = (10, SCREEN_HEIGHT - 10) # Positioned at bottom-left
        screen.blit(ammo_text_surface, ammo_text_rect)
        # --- End Ammo Count ---

        # --- NEW: Controls Text (Bottom Right) ---
        draw_text_lines(screen, controls_text_lines, small_font, WHITE, (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        # --- End Controls Text ---

    elif game_state == START:
        # START screen
        screen.fill(GREEN)
        title_text = font.render("Cognizant Moto-GP", True, BLACK)
        start_prompt = font.render("Press SPACE to Start", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        start_rect = start_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(title_text, title_rect)
        screen.blit(start_prompt, start_rect)
        # Draw start controls
        draw_text_lines(screen, start_controls_text_lines, small_font, BLACK, (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))


    elif game_state == GAME_OVER:
         # GAME_OVER screen
        screen.fill(RED)
        go_text = font.render("Game Over!", True, BLACK)
        restart_prompt = font.render("Press R to Restart", True, BLACK)
        final_score = font.render(f"Final Score: {score}", True, BLACK)
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        restart_rect = restart_prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        screen.blit(go_text, go_rect)
        screen.blit(final_score, score_rect)
        screen.blit(restart_prompt, restart_rect)
        # Draw game over controls
        draw_text_lines(screen, game_over_controls_text_lines, small_font, BLACK, (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))


    # Refresh screen & Cap FPS
    pygame.display.flip()
    clock.tick(30) # Target 30 FPS

# Quit Pygame
print("Exiting game.")
pygame.quit()