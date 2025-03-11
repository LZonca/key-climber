import os
import time

import pygame
import random
import threading
import json

from model.Difficulty import Difficulty
from model.DifficultySelector import DifficultySelector
from model.Slider import Slider
from model.Background import Background
from model.Lava import Lava
from model.Player import Player
from model.Obstacle import Obstacle
from model.Settings import Settings

os.environ['SDL_VIDEO_CENTERED'] = '1'

# Keys
AVAILABLE_KEYS = ["A", "S", "D", "W", "Z", "Q", "E", "R", "T", "Y", "U", "I", "O", "P", "F", "G", "H", "J", "K", "L", "X", "C", "V", "B", "N", "M"]
MAX_ROCK_IMG = 4
TAUX_PIEGES = 0.2
NB_VIES = 4
MAX_BLACK_SQUARES = 20  # Decreased from 30
MAX_OBSTACLES = 20  # Set the maximum number of obstacles
BLACK_SQUARE_SPAWN_RATE = 20  # Increased from 10
LAVA_SPEED = 0.5

pygame.init()

screen_info = pygame.display.Info()
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Jeu d'Escalade")

screen_rect = screen.get_rect()
screen_center = (pygame.display.Info().current_w // 2 - screen_rect.width // 2,
                 pygame.display.Info().current_h // 2 - screen_rect.height // 2)
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{screen_center[0]},{screen_center[1]}"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)


font = pygame.font.Font(None, 36)

# Load sounds
wrong_key_sound = pygame.mixer.Sound('./ressources/wrong_key.mp3')
faster_sound = pygame.mixer.Sound('./ressources/faster.wav')

# Thread for music
def play_music():
    pygame.mixer.music.load('./ressources/musique.mp3')
    pygame.mixer.music.play(-1)

music_thread = threading.Thread(target=play_music)
music_thread.start()

def play_faster_sound():
    faster_sound.play()

def play_wrong_key_sound():
    wrong_key_sound.play()

class Game:
    def __init__(self):
        self.settings = Settings('./settings.xml')
        self.player = Player(WIDTH, HEIGHT)
        self.obstacles = []
        self.score = 0
        self.lives = NB_VIES
        self.clock = pygame.time.Clock()
        self.running = True
        self.available_keys = AVAILABLE_KEYS.copy()
        self.difficulty = self.load_difficulty(self.settings.settings['difficulty'])
        self.rock_image = None
        self.game_over = False
        self.background = Background('./ressources/background.jpg', WIDTH, HEIGHT )
        self.scores_file = './scores.json'
        self.high_scores = self.load_scores()
        self.lava = Lava(WIDTH, HEIGHT, LAVA_SPEED, "./ressources/lava.jpg")
        self.apply_settings()
        self.spawn_rate = self.get_initial_spawn_rate()
        self.background_image = pygame.image.load('./ressources/menu.jpg')
        self.background_image = pygame.transform.scale(self.background_image, (WIDTH, HEIGHT))
    def get_initial_spawn_rate(self):
        if self.difficulty == 'easy':
            return 70  # Increased from 50
        elif self.difficulty == 'medium':
            return 50  # Increased from 30
        elif self.difficulty == 'hard':
            return 30  # Increased from 20
        else:
            return 50  # Default value in case of an unknown difficulty

    def adjust_difficulty(self):
        # Adjust spawn rate based on score and distance to lava
        distance_to_lava = self.player.rect.bottom - self.lava.rect.top
        if self.score < 100:
            self.spawn_rate = self.get_initial_spawn_rate()
        elif self.score < 200:
            self.spawn_rate = max(10, self.spawn_rate - 1)
        else:
            self.spawn_rate = max(5, self.spawn_rate - 1)

        if distance_to_lava < 100:
            self.spawn_rate = max(5, self.spawn_rate - 2)

    def load_difficulty(self, difficulty_name):
        difficulties = {
            'easy': Difficulty('easy', obstacle_speed=2, spawn_rate=70, lava_speed_increment=0.03),  # Decreased speed
            'medium': Difficulty('medium', obstacle_speed=4, spawn_rate=50, lava_speed_increment=0.07),
            # Decreased speed
            'hard': Difficulty('hard', obstacle_speed=6, spawn_rate=30, lava_speed_increment=0.15)  # Decreased speed
        }
        return difficulties.get(difficulty_name, difficulties['medium'])

    def apply_settings(self):
        pygame.mixer.music.set_volume(self.settings.settings['volume'])
        display_mode = self.settings.settings['display_mode']
        if display_mode == 'fullscreen':
            pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        elif display_mode == 'borderless':
            pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
        else:
            pygame.display.set_mode((WIDTH, HEIGHT))

        # Apply font size to obstacles text
        global obstacle_font
        obstacle_font = pygame.font.Font(None, int(self.settings.settings['font_size']))

        # Apply square size to obstacles
        self.obstacle_size = int(self.settings.settings['square_size'])

        # Apply spawn rate from settings
        self.spawn_rate = int(self.settings.settings.get('spawn_rate', BLACK_SQUARE_SPAWN_RATE))

    def load_scores(self):
        if not os.path.exists(self.scores_file):
            with open(self.scores_file, 'w') as file:
                json.dump([0] * 10, file)
        try:
            with open(self.scores_file, 'r') as file:
                scores = json.load(file)
                if not scores:
                    return [0] * 10
                return scores
        except (FileNotFoundError, json.JSONDecodeError):
            return [0] * 10

    def save_scores(self):
        try:
            with open(self.scores_file, 'w') as file:
                json.dump(self.high_scores, file)
            print(f"Scores successfully saved: {self.high_scores}")
        except Exception as e:
            print(f"Error saving scores: {e}")

    def update_high_scores(new_score):
        # Path to the scores file
        scores_file = "scores.json"

        try:
            # Read existing scores
            if os.path.exists(scores_file):
                with open(scores_file, 'r') as f:
                    scores = json.load(f)
            else:
                scores = []

            # Add new score
            scores.append(new_score)

            # Sort scores in descending order
            scores.sort(reverse=True)

            # Keep only top 10 scores
            scores = scores[:10]

            # Save updated scores back to the file
            with open(scores_file, 'w') as f:
                json.dump(scores, f)

            return scores

        except Exception as e:
            print(f"Error updating high scores: {e}")
            return []

    def show_menu(self):
        menu_running = True
        difficulty_selector = DifficultySelector(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 40,
                                                 ['easy', 'medium', 'hard'], self.settings.settings['difficulty'])

        while menu_running:
            screen.blit(self.background_image, (0, 0))  # Draw the background image
            title_text = font.render("Main Menu", True, BLACK)
            start_text = font.render("Press S to Start", True, BLACK)
            quit_text = font.render("Press Q to Quit", True, BLACK)
            settings_text = font.render("Press T for Settings", True, BLACK)

            title_x = WIDTH // 2 - title_text.get_width() // 2
            title_y = HEIGHT // 2 - 200
            start_x = WIDTH // 2 - start_text.get_width() // 2
            start_y = HEIGHT // 2
            quit_x = WIDTH // 2 - quit_text.get_width() // 2
            quit_y = HEIGHT // 2 + 50
            settings_x = WIDTH // 2 - settings_text.get_width() // 2
            settings_y = HEIGHT // 2 + 100

            # Function to draw text with border
            def draw_text_with_border(text, x, y):
                border_color = (255, 255, 255)  # White border color
                screen.blit(font.render(text, True, border_color), (x - 2, y - 2))
                screen.blit(font.render(text, True, border_color), (x + 2, y - 2))
                screen.blit(font.render(text, True, border_color), (x - 2, y + 2))
                screen.blit(font.render(text, True, border_color), (x + 2, y + 2))
                screen.blit(font.render(text, True, BLACK), (x, y))  # Main text

            draw_text_with_border("Main Menu", title_x, title_y)
            draw_text_with_border("Press S to Start", start_x, start_y)
            draw_text_with_border("Press Q to Quit", quit_x, quit_y)
            draw_text_with_border("Press T for Settings", settings_x, settings_y)

            difficulty_selector.draw(screen)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    menu_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        self.settings.settings['difficulty'] = difficulty_selector.get_current_difficulty()
                        self.settings.save_settings()
                        self.apply_settings()
                        menu_running = False
                    if event.key == pygame.K_q:
                        self.running = False
                        menu_running = False
                    if event.key == pygame.K_t:
                        self.show_settings_menu()
                difficulty_selector.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if start_x <= mouse_pos[0] <= start_x + start_text.get_width() and start_y <= mouse_pos[
                        1] <= start_y + start_text.get_height():
                        self.settings.settings['difficulty'] = difficulty_selector.get_current_difficulty()
                        self.settings.save_settings()
                        self.apply_settings()
                        menu_running = False
                    if quit_x <= mouse_pos[0] <= quit_x + quit_text.get_width() and quit_y <= mouse_pos[
                        1] <= quit_y + quit_text.get_height():
                        self.running = False
                        menu_running = False
                    if settings_x <= mouse_pos[0] <= settings_x + settings_text.get_width() and settings_y <= mouse_pos[
                        1] <= settings_y + settings_text.get_height():
                        self.show_settings_menu()

    def generate_obstacle(self):
        if len(self.obstacles) >= MAX_OBSTACLES:
            return  # Do not generate more obstacles if the limit is reached

        if not self.available_keys:
            self.available_keys = AVAILABLE_KEYS.copy()
        is_trap = random.random() < TAUX_PIEGES
        if is_trap:
            available_keys_for_trap = [key for key in self.available_keys if
                                       key not in [obs.key for obs in self.obstacles if not obs.is_trap]]
            if available_keys_for_trap:
                key = random.choice(available_keys_for_trap)
                self.available_keys.remove(key)
            else:
                return  # No available keys for traps, skip generating this obstacle
        else:
            if len([obs for obs in self.obstacles if not obs.is_trap]) >= MAX_BLACK_SQUARES:
                return
            available_keys_for_correct = [key for key in self.available_keys if
                                          key not in [obs.key for obs in self.obstacles if obs.is_trap]]
            if available_keys_for_correct:
                key = random.choice(available_keys_for_correct)
                self.available_keys.remove(key)
            else:
                return  # No available keys for correct obstacles, skip generating this obstacle
        self.obstacles.append(Obstacle(WIDTH, is_trap, key, self.obstacle_size, self.difficulty.obstacle_speed))

    def reset_game(self):
        self.update_high_scores()
        self.player = Player(WIDTH, HEIGHT)
        self.obstacles = []
        self.score = 0
        self.lives = NB_VIES
        self.available_keys = AVAILABLE_KEYS.copy()
        self.rock_image = None
        self.game_over = False
        self.lava.reset_position()

    def handle_key_press(self, key):
        for obstacle in self.obstacles:
            if key == obstacle.key:
                if obstacle.is_trap:
                    sound_thread = threading.Thread(target=play_wrong_key_sound)
                    sound_thread.start()
                    rock_thread = threading.Thread(target=self.display_rock_image)
                    rock_thread.start()
                    if self.lives <= 0:
                        self.game_over = True
                    self.lives -= 1
                else:
                    self.score += 10
                    self.player.climb()  # Move the player up
                    self.background.move(self.player.rect, HEIGHT)  # Move background down
                    self.lava.moving_up = False  # Ensure lava starts moving down
                    self.lava.move_down(50)  # Move lava down by 50 units

                self.obstacles.remove(obstacle)
                break

    def log_positions(self):
        player_pos = (self.player.rect.x, self.player.rect.y)
        lava_pos = (self.lava.rect.x, self.lava.rect.y)
        print(f"Player Position: {player_pos}, Lava Position: {lava_pos}")

    def display_positions(self, screen):
        player_pos_text = font.render(f"Player: {self.player.rect.topleft}", True, BLACK)
        lava_pos_text = font.render(f"Lava: {self.lava.rect.topleft}", True, BLACK)
        screen.blit(player_pos_text, (20, 100))
        screen.blit(lava_pos_text, (20, 140))

    def pause_menu(self):
        paused = True
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Fill with black color and set transparency level (0-255)

        while paused:
            screen.blit(overlay, (0, 0))  # Draw the semi-transparent overlay
            pause_text = font.render("Paused", True, (255, 255, 255))
            resume_text = font.render("Press ESC to Resume", True, (255, 255, 255))
            main_menu_text = font.render("Press M for Main Menu", True, (255, 255, 255))
            screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(resume_text, (WIDTH // 2 - resume_text.get_width() // 2, HEIGHT // 2))
            screen.blit(main_menu_text, (WIDTH // 2 - main_menu_text.get_width() // 2, HEIGHT // 2 + 50))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    paused = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        paused = False
                    if event.key == pygame.K_m:
                        self.show_menu()
                        paused = False

    def display_rock_image(self):
        rock_number = random.randint(1, MAX_ROCK_IMG)
        rock_image_path = f'./ressources/rocks/rock{rock_number}.jpeg'
        try:
            self.rock_image = pygame.image.load(rock_image_path)
            self.rock_image = pygame.transform.scale(self.rock_image, (WIDTH, HEIGHT))  # Resize to 100x100 pixels
            self.rock_display_time = time.time() + 1
        except pygame.error as e:
            print(f"Failed to load image at {rock_image_path}: {e}")
            self.rock_image = None

    def display_game_over(self):
        game_over_text = font.render("Fin de la partie", True, RED)
        restart_text = font.render("Appuyer sur R pour redémarrer", True, RED)
        menu_text = font.render("Appuyer sur M pour le menu", True, RED)
        user_score_text = font.render(f"Votre score: {self.score}", True, BLACK)
        high_score_text = font.render(f"Score le plus hau: {self.high_scores[0]}", True, BLACK)

        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(user_score_text, (WIDTH // 2 - user_score_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()

    def show_settings_menu(self):
        volume_slider = Slider(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 20, 0.0, 1.0, self.settings.settings['volume'])
        font_size_slider = Slider(WIDTH // 2 - 100, HEIGHT // 2, 200, 20, 10, 100, self.settings.settings['font_size'])
        square_size_slider = Slider(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 20, 10, 100,
                                    self.settings.settings['square_size'])

        settings_running = True
        while settings_running:
            screen.blit(self.background_image, (0, 0))  # Draw the background image
            title_text = font.render("Settings", True, BLACK)
            back_text = font.render("Press B to go back", True, BLACK)
            validate_text = font.render("Press V to Validate", True, BLACK)

            title_x = WIDTH // 2 - title_text.get_width() // 2
            title_y = HEIGHT // 2 - 200
            back_x = WIDTH // 2 - back_text.get_width() // 2
            back_y = HEIGHT // 2 + 200
            validate_x = WIDTH // 2 - validate_text.get_width() // 2
            validate_y = back_y + 50

            # Function to draw text with border
            def draw_text_with_border(text, x, y):
                border_color = (255, 255, 255)  # White border color
                screen.blit(font.render(text, True, border_color), (x - 2, y - 2))
                screen.blit(font.render(text, True, border_color), (x + 2, y - 2))
                screen.blit(font.render(text, True, border_color), (x - 2, y + 2))
                screen.blit(font.render(text, True, border_color), (x + 2, y + 2))
                screen.blit(font.render(text, True, BLACK), (x, y))  # Main text

            draw_text_with_border("Settings", title_x, title_y)
            draw_text_with_border("Press B to go back", back_x, back_y)
            draw_text_with_border("Press V to Validate", validate_x, validate_y)

            volume_slider.draw(screen)
            font_size_slider.draw(screen)
            square_size_slider.draw(screen)

            volume_label = font.render(f"Volume: {volume_slider.value:.2f}", True, BLACK)
            font_size_label = font.render(f"Font Size: {font_size_slider.value:.0f}", True, BLACK)
            square_size_label = font.render(f"Square Size: {square_size_slider.value:.0f}", True, BLACK)

            screen.blit(volume_label, (volume_slider.rect.x, volume_slider.rect.y - 30))
            screen.blit(font_size_label, (font_size_slider.rect.x, font_size_slider.rect.y - 30))
            screen.blit(square_size_label, (square_size_slider.rect.x, square_size_slider.rect.y - 30))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    settings_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        settings_running = False
                    if event.key == pygame.K_v:
                        self.settings.settings['volume'] = volume_slider.value
                        self.settings.settings['font_size'] = font_size_slider.value
                        self.settings.settings['square_size'] = square_size_slider.value
                        self.settings.save_settings()
                        self.apply_settings()  # Apply the new settings
                        print(
                            f"Settings applied: Volume={volume_slider.value}, Font Size={font_size_slider.value}, Square Size={square_size_slider.value}")
                        settings_running = False
                volume_slider.handle_event(event)
                font_size_slider.handle_event(event)
                square_size_slider.handle_event(event)

    def run(self):
        try:
            self.show_menu()
            while self.running:
                screen.fill(WHITE)

                if not self.game_over:
                    self.background.draw(screen)

                    self.adjust_difficulty()

                    self.generate_obstacle()

                    for obstacle in self.obstacles:
                        obstacle.move_down()
                        if obstacle.pos[1] > HEIGHT:
                            if not obstacle.is_trap:
                                sound_thread = threading.Thread(target=play_faster_sound)
                                sound_thread.start()
                            self.obstacles.remove(obstacle)
                        obstacle.draw(screen, font)

                    self.player.draw(screen)
                    self.lava.update_position()  # Update lava position smoothly
                    self.lava.draw(screen)

                    self.background.move(self.player.rect, HEIGHT)

                    if self.rock_image and time.time() < self.rock_display_time:
                        screen.blit(self.rock_image, (
                            WIDTH // 2 - self.rock_image.get_width() // 2,
                            HEIGHT // 2 - self.rock_image.get_height() // 2))
                    else:
                        self.rock_image = None

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                self.pause_menu()
                            else:
                                self.handle_key_press(event.unicode.upper())

                    score_text = font.render(f"Score: {self.score}", True, BLACK)
                    screen.blit(score_text, (20, 20))

                    lives_text = font.render(f"Lives: {self.lives}", True, BLACK)
                    screen.blit(lives_text, (20, 60))

                    if self.player.rect.bottom > self.lava.rect.top:
                        self.game_over = True

                    self.log_positions()
                    self.display_positions(screen)

                    # Increase lava speed based on score or time
                    if self.score % 100 == 0 and self.score != 0:
                        self.lava.increase_speed(self.difficulty.lava_speed_increment)

                else:
                    self.display_game_over()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_r:
                                self.reset_game()
                            if event.key == pygame.K_m:
                                self.show_menu()
                                self.reset_game()

                pygame.display.flip()
                self.clock.tick(20)
        except KeyboardInterrupt:
            print("Game interrupted by user.")
        finally:
            pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()