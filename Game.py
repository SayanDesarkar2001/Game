import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Playable Area
PLAYABLE_WIDTH = 700
ROAD_LEFT_BOUNDARY = (SCREEN_WIDTH - PLAYABLE_WIDTH) // 2
ROAD_RIGHT_BOUNDARY = ROAD_LEFT_BOUNDARY + PLAYABLE_WIDTH

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Game states
START, PLAYING, GAME_OVER = 0, 1, 2

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Endless Bike Racing Game")

# --- Asset Loading ---
try:
    bike_image = pygame.image.load('bike.png').convert_alpha()
    obstacle_image = pygame.image.load('obstacle.png').convert_alpha()
    boost_image = pygame.image.load('boost.png').convert_alpha()
    road_image = pygame.image.load('road.png').convert()

    # Load Individual Explosion Images
    explosion_files = [
        'explosion1.png',
        'explosion2.png',
        'explosion3.png',
        'explosion4.png',
        'explosion5.png'
    ]
    explosion_anim = []
    EXPLOSION_SCALE_FACTOR = 1.0 # Adjust if needed (1.0 = original size)

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
            # Skipping missing frame

    if not explosion_anim:
         raise pygame.error("No explosion animation frames loaded successfully!")

except pygame.error as e:
    print(f"Error loading assets: {e}")
    print("Ensure 'bike.png', 'obstacle.png', 'boost.png', 'road.png', and the")
    print("explosion image files ('explosion1.png' to 'explosion5.png') are in the same directory.")
    pygame.quit()
    exit()


# Scale images (Obstacle scaling is crucial)
bike_image = pygame.transform.scale(bike_image, (75, 150))
obstacle_image = pygame.transform.scale(obstacle_image, (50, 50)) # Ensure this is 50x50
boost_image = pygame.transform.scale(boost_image, (50, 50))
road_image = pygame.transform.scale(road_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# --- Sound Loading ---
try:
    laser_sound = pygame.mixer.Sound('laser.wav')
    explosion_sound = pygame.mixer.Sound('explosion.wav')
    boost_sound = pygame.mixer.Sound('boost.wav')
except pygame.error as e:
    print(f"Error loading sound: {e}")
    print("Ensure 'laser.wav', 'explosion.wav', and 'boost.wav' are in the same directory.")
    laser_sound = None
    explosion_sound = None
    boost_sound = None

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
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.speed = 5
        self.boosted = False
        self.boost_timer = 0

    def update(self):
        keys = pygame.key.get_pressed()
        current_speed = self.speed * 1.5 if self.boosted else self.speed
        if keys[pygame.K_LEFT] and self.rect.left > ROAD_LEFT_BOUNDARY:
            self.rect.x -= current_speed
        if keys[pygame.K_RIGHT] and self.rect.right < ROAD_RIGHT_BOUNDARY:
            self.rect.x += current_speed
        if self.rect.left < ROAD_LEFT_BOUNDARY:
            self.rect.left = ROAD_LEFT_BOUNDARY
        if self.rect.right > ROAD_RIGHT_BOUNDARY:
            self.rect.right = ROAD_RIGHT_BOUNDARY

    def shoot(self):
        laser = Laser(self.rect.centerx, self.rect.top)
        all_sprites.add(laser)
        lasers.add(laser)
        play_sound(laser_sound)

    def reset(self):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.speed = 5
        self.boosted = False
        self.boost_timer = 0


class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = obstacle_image # Use the globally scaled image
        self.rect = self.image.get_rect()
        # --- Optional Debug Print (can be uncommented if needed) ---
        # print(f"DEBUG: Obstacle rect size on init: {self.rect.size}")
        # --- End Debug Print ---
        self.reset_position() # Call the fixed method below
        self.base_speed = 5
        self.speed = self.base_speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.reset_position()

    # --- FIXED reset_position Method ---
    def reset_position(self):
        # Calculate the maximum possible x value for the left edge
        # Ensure self.rect.width is valid (should be 50 from scaling)
        max_left_x = ROAD_RIGHT_BOUNDARY - self.rect.width

        # Ensure the upper bound of randint is at least the lower bound
        # This prevents ValueError if max_left_x accidentally becomes < ROAD_LEFT_BOUNDARY
        upper_bound = max(ROAD_LEFT_BOUNDARY, max_left_x)

        # Now, generate the random x position within the valid range
        try:
            self.rect.x = random.randint(ROAD_LEFT_BOUNDARY, upper_bound)
        except ValueError as e:
             # This should ideally not happen with the max() check, but provides fallback
             print(f"WARNING: Still encountered ValueError in randint({ROAD_LEFT_BOUNDARY}, {upper_bound}) despite fix. Error: {e}")
             print(f"         Obstacle rect width: {self.rect.width}")
             self.rect.x = ROAD_LEFT_BOUNDARY # Place at left boundary as fallback

        # The y position reset remains the same
        self.rect.y = random.randint(-SCREEN_HEIGHT, -self.rect.height)
    # --- End FIXED reset_position Method ---

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
        self.base_speed = 5
        self.speed = self.base_speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
             self.reset_position()

    def reset_position(self):
         # Similar check for boost item placement consistency
        max_left_x = ROAD_RIGHT_BOUNDARY - self.rect.width
        upper_bound = max(ROAD_LEFT_BOUNDARY, max_left_x)
        try:
            self.rect.x = random.randint(ROAD_LEFT_BOUNDARY, upper_bound)
        except ValueError:
             self.rect.x = ROAD_LEFT_BOUNDARY # Fallback

        self.rect.y = random.randint(-SCREEN_HEIGHT * 2, -self.rect.height)

    def set_speed(self, new_speed):
        self.speed = new_speed

    def reset_speed(self):
        self.speed = self.base_speed


class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, animation_frames):
        super().__init__()
        self.animation_frames = animation_frames
        if not self.animation_frames:
             self.kill()
             return
        self.image = self.animation_frames[0]
        self.rect = self.image.get_rect(center=center)
        self.frame_index = 0
        self.last_update_time = pygame.time.get_ticks()
        self.frame_rate_ms = 75 # Animation speed (milliseconds)

    def update(self):
        if not hasattr(self, 'animation_frames') or not self.animation_frames:
            self.kill()
            return

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
all_sprites = pygame.sprite.Group()

all_sprites.add(player)

# Populate initial sprites (Obstacle() now calls the fixed reset_position)
for _ in range(5):
    obstacle = Obstacle()
    obstacles.add(obstacle)
    all_sprites.add(obstacle)

for _ in range(1):
    boost = Boost()
    boosts.add(boost)
    all_sprites.add(boost)

score = 0
font = pygame.font.Font(None, 36)

background_y = 0
base_background_speed = 5
background_speed = base_background_speed

running = True
clock = pygame.time.Clock()
game_state = START
boost_duration = 180
boost_speed_multiplier = 2

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
                    player.shoot()
            elif game_state == GAME_OVER:
                if event.key == pygame.K_r:
                    game_state = START
                    score = 0
                    player.reset()
                    background_speed = base_background_speed
                    background_y = 0
                    # Clear all non-player sprites
                    for sprite in all_sprites:
                         if sprite != player:
                             sprite.kill()
                    # Repopulate
                    for _ in range(5):
                        obstacle = Obstacle(); obstacles.add(obstacle); all_sprites.add(obstacle)
                    for _ in range(1):
                        boost = Boost(); boosts.add(boost); all_sprites.add(boost)

    # Game State Logic
    if game_state == PLAYING:
        all_sprites.update() # Update player, obstacles, boosts, lasers, explosions

        # Boost handling
        if player.boosted:
            player.boost_timer -= 1
            if player.boost_timer <= 0:
                player.boosted = False
                background_speed = base_background_speed
                for obstacle in obstacles: obstacle.reset_speed()
                for boost in boosts: boost.reset_speed()

        # Collision: Player vs Obstacles
        if pygame.sprite.spritecollideany(player, obstacles):
            play_sound(explosion_sound) # Use explosion sound for player crash too
            game_state = GAME_OVER

        # Collision: Player vs Boosts
        collected_boosts = pygame.sprite.spritecollide(player, boosts, True)
        if collected_boosts:
            player.boosted = True; player.boost_timer = boost_duration; play_sound(boost_sound)
            boosted_speed = base_background_speed * boost_speed_multiplier; background_speed = boosted_speed
            # Speed up existing items
            for obstacle in obstacles: obstacle.set_speed(obstacle.base_speed * boost_speed_multiplier)
            for boost_item in boosts: boost_item.set_speed(boost_item.base_speed * boost_speed_multiplier)
            # Add new boost (will also get correct speed via its own logic if needed)
            new_boost = Boost()
            if player.boosted: new_boost.set_speed(new_boost.base_speed * boost_speed_multiplier) # Set speed if boost active
            boosts.add(new_boost); all_sprites.add(new_boost)

        # Collision: Lasers vs Obstacles
        hits = pygame.sprite.groupcollide(lasers, obstacles, False, False) # Detect without auto-killing
        for laser, hit_obstacles_list in hits.items():
            laser.kill() # Kill the laser
            for obstacle in hit_obstacles_list:
                score += 10
                play_sound(explosion_sound) # Explosion sound for hitting obstacle
                explosion = Explosion(obstacle.rect.center, explosion_anim)
                all_sprites.add(explosion)
                obstacle.kill() # Kill the hit obstacle
                # Respawn obstacle
                new_obstacle = Obstacle()
                if player.boosted: new_obstacle.set_speed(new_obstacle.base_speed * boost_speed_multiplier) # Set speed if boost active
                obstacles.add(new_obstacle); all_sprites.add(new_obstacle)

        # Score update & Background scroll
        score += 1
        background_y += background_speed
        if background_y >= SCREEN_HEIGHT: background_y = 0

        # --- Draw ---
        screen.blit(road_image, (0, background_y))
        screen.blit(road_image, (0, background_y - SCREEN_HEIGHT))
        all_sprites.draw(screen) # Draw everything (player, items, explosions)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

    elif game_state == START:
        # START screen
        screen.fill(GREEN)
        start_text = font.render("Press SPACE to Start", True, BLACK)
        text_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(start_text, text_rect)

    elif game_state == GAME_OVER:
         # GAME_OVER screen
        screen.fill(RED)
        game_over_text = font.render("Game Over!", True, BLACK)
        restart_text = font.render("Press R to Restart", True, BLACK)
        final_score_text = font.render(f"Final Score: {score}", True, BLACK)
        go_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        screen.blit(game_over_text, go_rect)
        screen.blit(final_score_text, score_rect)
        screen.blit(restart_text, restart_rect)

    # Refresh screen & Cap FPS
    pygame.display.flip()
    clock.tick(30)

# Quit Pygame
pygame.quit()