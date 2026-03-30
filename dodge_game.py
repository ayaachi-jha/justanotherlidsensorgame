import pygame
import random
import sys
from pybooklid import LidSensor

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SIZE = 40
OBSTACLE_WIDTH = 50
OBSTACLE_HEIGHT = 50
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (200, 0, 255)

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 100
        self.size = PLAYER_SIZE
        self.sensitivity = 3  # Multiplier for lid angle changes
        
    def update_position(self, lid_angle):
        # Map lid angle to smaller range for finer control
        # Use only a portion of the angle range (e.g., 60-120°) mapped to full screen
        angle = max(60, min(120, lid_angle))
        normalized = (angle - 60) / 60  # 0 to 1
        self.x = normalized * (SCREEN_WIDTH - self.size)
        
    def draw(self, screen):
        # Draw bike wheels
        wheel_radius = 8
        pygame.draw.circle(screen, BLACK, (int(self.x + 10), int(self.y + 35)), wheel_radius)
        pygame.draw.circle(screen, BLACK, (int(self.x + 30), int(self.y + 35)), wheel_radius)
        
        # Draw bike frame
        pygame.draw.line(screen, BLACK, (int(self.x + 10), int(self.y + 35)), (int(self.x + 20), int(self.y + 20)), 3)
        pygame.draw.line(screen, BLACK, (int(self.x + 20), int(self.y + 20)), (int(self.x + 30), int(self.y + 35)), 3)
        pygame.draw.line(screen, BLACK, (int(self.x + 20), int(self.y + 20)), (int(self.x + 20), int(self.y + 10)), 3)
        
        # Draw person body
        pygame.draw.circle(screen, (255, 200, 150), (int(self.x + 20), int(self.y + 5)), 5)  # Head
        pygame.draw.line(screen, BLUE, (int(self.x + 20), int(self.y + 10)), (int(self.x + 20), int(self.y + 20)), 3)  # Body
        pygame.draw.line(screen, BLUE, (int(self.x + 20), int(self.y + 15)), (int(self.x + 15), int(self.y + 25)), 2)  # Left arm
        pygame.draw.line(screen, BLUE, (int(self.x + 20), int(self.y + 15)), (int(self.x + 25), int(self.y + 25)), 2)  # Right arm
        pygame.draw.line(screen, BLACK, (int(self.x + 20), int(self.y + 20)), (int(self.x + 15), int(self.y + 32)), 2)  # Left leg
        pygame.draw.line(screen, BLACK, (int(self.x + 20), int(self.y + 20)), (int(self.x + 25), int(self.y + 32)), 2)  # Right leg

class Obstacle:
    def __init__(self, difficulty=1):
        self.x = random.randint(0, SCREEN_WIDTH - OBSTACLE_WIDTH)
        self.y = -OBSTACLE_HEIGHT
        self.width = OBSTACLE_WIDTH * 1.5  # Cars are wider
        self.height = OBSTACLE_HEIGHT * 1.5  # Cars are taller
        self.speed = random.uniform(3.0, 5.0 + difficulty)
        
        # Random car types
        self.type = random.choice(['sedan', 'truck', 'sports', 'taxi'])
        
        if self.type == 'sports':
            self.speed *= 1.5
            self.color = RED
            self.width = OBSTACLE_WIDTH * 1.2
        elif self.type == 'truck':
            self.width = OBSTACLE_WIDTH * 2
            self.height = OBSTACLE_HEIGHT * 2
            self.color = (100, 100, 100)
        elif self.type == 'taxi':
            self.color = YELLOW
        else:
            self.color = (50, 50, 200)
        
    def update(self):
        self.y += self.speed
        
    def draw(self, screen):
        # Draw car body
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), int(self.width), int(self.height)))
        
        # Draw car windows
        window_color = (150, 200, 255)
        window_height = self.height * 0.3
        pygame.draw.rect(screen, window_color, (int(self.x + 5), int(self.y + 5), int(self.width - 10), int(window_height)))
        
        # Draw wheels
        wheel_size = 6
        pygame.draw.circle(screen, BLACK, (int(self.x + 10), int(self.y + self.height - 5)), wheel_size)
        pygame.draw.circle(screen, BLACK, (int(self.x + self.width - 10), int(self.y + self.height - 5)), wheel_size)
        
    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT
        
    def collides_with(self, player):
        return (self.x < player.x + player.size and
                self.x + self.width > player.x and
                self.y < player.y + player.size and
                self.y + self.height > player.y)

class Collectible:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH - 30)
        self.y = -30
        self.size = 25
        self.speed = 3
        
    def update(self):
        self.y += self.speed
        
    def draw(self, screen):
        # Draw coin/power-up
        pygame.draw.circle(screen, YELLOW, (int(self.x + self.size // 2), int(self.y + self.size // 2)), self.size // 2)
        pygame.draw.circle(screen, (255, 215, 0), (int(self.x + self.size // 2), int(self.y + self.size // 2)), self.size // 3)
        
    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT
        
    def collides_with(self, player):
        center_x = self.x + self.size // 2
        center_y = self.y + self.size // 2
        return (center_x > player.x and center_x < player.x + player.size and
                center_y > player.y and center_y < player.y + player.size)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Bike Dodge - Avoid the Traffic!")
    clock = pygame.time.Clock()
    
    # Create sound effects using simpler method
    def make_tone(frequency, duration):
        sample_rate = 22050
        max_amplitude = 2 ** (16 - 1) - 1
        samples = int(sample_rate * duration)
        wave = [int(max_amplitude * 0.5 * ((i // (sample_rate // frequency // 2)) % 2 * 2 - 1)) for i in range(samples)]
        stereo_wave = [[sample, sample] for sample in wave]
        sound = pygame.sndarray.make_sound(stereo_wave)
        return sound
    
    sounds_enabled = False
    collision_sound = None
    collect_sound = None
    gameover_sound = None
    
    try:
        # Test if sndarray is available
        import pygame.sndarray as sndarray
        
        # Create simple beep sounds
        collision_sound = make_tone(300, 0.2)
        collect_sound = make_tone(800, 0.15)
        gameover_sound = make_tone(150, 0.5)
        
        # Set volume
        collision_sound.set_volume(0.5)
        collect_sound.set_volume(0.4)
        gameover_sound.set_volume(0.6)
        
        sounds_enabled = True
        print("✓ Sound enabled!")
    except Exception as e:
        print(f"✗ Sound disabled: {e}")
        print("Install numpy for sound: pip install numpy")
    
    # Initialize sensor
    sensor = LidSensor(auto_connect=False)
    try:
        sensor.connect()
        print("Sensor connected! Tilt your laptop lid to move.")
    except Exception as e:
        print(f"Failed to connect sensor: {e}")
        print("Using mouse for testing...")
        sensor = None
    
    player = Player()
    obstacles = []
    collectibles = []
    score = 0
    lives = 3
    game_over = False
    
    # Spawn timers
    spawn_timer = 0
    spawn_interval = 60
    collectible_timer = 0
    collectible_interval = 180
    
    difficulty = 1
    
    current_angle = 90  # Default middle position
    
    # Start monitoring sensor in a separate thread
    sensor_active = sensor is not None
    
    def update_angle(angle):
        nonlocal current_angle
        current_angle = angle
    
    running = True
    try:
        while running:
            clock.tick(FPS)
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and game_over:
                        # Restart game
                        player = Player()
                        obstacles = []
                        collectibles = []
                        score = 0
                        lives = 3
                        game_over = False
                        spawn_timer = 0
                        collectible_timer = 0
                        difficulty = 1
            
            if not game_over:
                # Get lid angle
                if sensor:
                    try:
                        # Read current angle directly
                        angle = sensor.read_angle()
                        if angle is not None:
                            current_angle = angle
                    except Exception as e:
                        print(f"Sensor error: {e}")
                else:
                    # Fallback: use mouse position for testing
                    mouse_x, _ = pygame.mouse.get_pos()
                    current_angle = (mouse_x / SCREEN_WIDTH) * 180
                
                # Update player position
                player.update_position(current_angle)
                
                # Spawn obstacles
                spawn_timer += 1
                if spawn_timer >= spawn_interval:
                    obstacles.append(Obstacle(difficulty))
                    spawn_timer = 0
                    spawn_interval = max(30, spawn_interval - 1)
                
                # Spawn collectibles
                collectible_timer += 1
                if collectible_timer >= collectible_interval:
                    collectibles.append(Collectible())
                    collectible_timer = 0
                
                # Update obstacles
                for obstacle in obstacles[:]:
                    obstacle.update()
                    
                    # Check collision
                    if obstacle.collides_with(player):
                        lives -= 1
                        obstacles.remove(obstacle)
                        if sounds_enabled:
                            collision_sound.play()
                        if lives <= 0:
                            game_over = True
                            if sounds_enabled:
                                gameover_sound.play()
                    
                    # Remove off-screen obstacles
                    if obstacle.is_off_screen():
                        obstacles.remove(obstacle)
                        score += 1
                        
                        # Increase difficulty every 20 points
                        if score % 20 == 0:
                            difficulty += 0.5
                
                # Update collectibles
                for collectible in collectibles[:]:
                    collectible.update()
                    
                    # Check collection
                    if collectible.collides_with(player):
                        collectibles.remove(collectible)
                        score += 5
                        lives = min(5, lives + 1)  # Max 5 lives
                        if sounds_enabled:
                            collect_sound.play()
                    
                    # Remove off-screen collectibles
                    if collectible.is_off_screen():
                        collectibles.remove(collectible)
            
            # Drawing
            screen.fill((100, 100, 100))  # Gray road
            
            # Draw road lines
            for i in range(0, SCREEN_HEIGHT, 40):
                pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 - 2, i, 4, 20))
            
            # Draw player
            player.draw(screen)
            
            # Draw obstacles
            for obstacle in obstacles:
                obstacle.draw(screen)
            
            # Draw collectibles
            for collectible in collectibles:
                collectible.draw(screen)
            
            # Draw score and lives
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Score: {score}", True, WHITE)
            lives_text = font.render(f"Lives: {lives}", True, RED if lives <= 1 else WHITE)
            screen.blit(score_text, (10, 10))
            screen.blit(lives_text, (10, 50))
            
            # Game over screen
            if game_over:
                game_over_font = pygame.font.Font(None, 72)
                game_over_text = game_over_font.render("GAME OVER", True, RED)
                restart_text = font.render("Press SPACE to restart", True, WHITE)
                screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))
                screen.blit(restart_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 20))
            
            pygame.display.flip()
    
    finally:
        if sensor:
            sensor.disconnect()
        pygame.quit()

if __name__ == "__main__":
    main()
