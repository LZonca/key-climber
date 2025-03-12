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
from model.InputBox import  InputBox

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
        self.background = Background('./ressources/background.jpg', WIDTH, HEIGHT)
        self.scores_file = './scores.json'
        self.high_scores = self.load_scores()
        self.lava = Lava(WIDTH, HEIGHT, LAVA_SPEED, "./ressources/lava.jpg")
        self.apply_settings()
        self.spawn_rate = self.get_initial_spawn_rate()
        self.background_image = pygame.image.load('./ressources/menu.jpg')
        self.background_image = pygame.transform.scale(self.background_image, (WIDTH, HEIGHT))
        self.player_name = "Anonymous"  # Default player name

    # Add this method to get player name
    def get_player_name(self):
        input_box = InputBox(WIDTH // 2 - 100, HEIGHT // 2, 200, 32, font)
        input_box.active = True  # Activate the input box immediately
        input_box.color = input_box.color_active  # Set active color

        name_entered = False
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Semi-transparent black

        while not name_entered and self.running:
            screen.blit(self.background_image, (0, 0))
            screen.blit(overlay, (0, 0))  # Add overlay

            prompt_text = font.render("Saisissez votre nom:", True, WHITE)
            screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 50))

            instruction_text = font.render("(Apuyer sur ENTRÉE pour valider)", True, WHITE)
            screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 2 + 40))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return "Annonyme"

                result = input_box.handle_event(event)
                if result is not None:  # Enter was pressed
                    name_entered = True
                    return result if result and result.strip() else "Annonyme"

            input_box.update()
            input_box.draw(screen)
            pygame.display.flip()
            self.clock.tick(30)

        return input_box.text if input_box.text and input_box.text.strip() else "Annonyme"

    def update_high_scores(self):
        try:
            if not os.path.exists(self.scores_file):
                with open(self.scores_file, 'w') as file:
                    json.dump([], file)

            with open(self.scores_file, 'r') as file:
                try:
                    scores = json.load(file)
                except json.JSONDecodeError:
                    scores = []

            # Add new entry with player name and difficulty
            new_entry = {
                "name": self.player_name,
                "score": self.score,
                "difficulty": self.settings.settings['difficulty']
            }

            # Only add if score is greater than 0
            if self.score > 0:
                scores.append(new_entry)

            # Sort scores by score value in descending order
            scores.sort(key=lambda x: x["score"] if isinstance(x, dict) else 0, reverse=True)

            # Keep only top 10 scores
            scores = scores[:10]

            # Save updated scores
            with open(self.scores_file, 'w') as file:
                json.dump(scores, file)

            self.high_scores = scores
            return scores
        except Exception as e:
            print(f"Error updating high scores: {e}")
            return []

    def get_initial_spawn_rate(self):
        if self.difficulty == 'facile':
            return 70  # Increased from 50
        elif self.difficulty == 'moyen':
            return 50  # Increased from 30
        elif self.difficulty == 'difficile':
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
            'facile': Difficulty('facile', obstacle_speed=2, spawn_rate=70, lava_speed_increment=0.03),  # Decreased speed
            'moyen': Difficulty('moyen', obstacle_speed=4, spawn_rate=50, lava_speed_increment=0.07),
            # Decreased speed
            'difficile': Difficulty('difficile', obstacle_speed=6, spawn_rate=30, lava_speed_increment=0.15)  # Decreased speed
        }
        return difficulties.get(difficulty_name, difficulties['moyen'])

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
        """Load scores from file with difficulty migration"""
        try:
            if os.path.exists(self.scores_file):
                with open(self.scores_file, 'r') as file:
                    scores = json.load(file)

                    # Migrate old scores without difficulty
                    updated = False
                    for score in scores:
                        if isinstance(score, dict) and 'difficulty' not in score:
                            score['difficulty'] = 'moyen'  # Default to medium
                            updated = True

                    if updated:
                        with open(self.scores_file, 'w') as update_file:
                            json.dump(scores, update_file)

                    return scores
            return []
        except Exception as e:
            print(f"Error loading scores: {e}")
            return []

    def save_scores(self):
        try:
            with open(self.scores_file, 'w') as file:
                json.dump(self.high_scores, file)
            print(f"Scores successfully saved: {self.high_scores}")
        except Exception as e:
            print(f"Error saving scores: {e}")

    def show_menu(self):
        self.reset_game()
        menu_running = True
        difficulty_selector = DifficultySelector(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 40,
                                                 ['facile', 'moyen', 'difficile'],
                                                 self.settings.settings['difficulty'])

        while menu_running:
            screen.blit(self.background_image, (0, 0))  # Draw the background image
            title_text = font.render("Menu Principal", True, BLACK)
            start_text = font.render("Appuyez sur S pour Commencer", True, BLACK)
            quit_text = font.render("Appuyez sur Q pour Quitter", True, BLACK)
            settings_text = font.render("Appuyez sur T pour les Paramètres", True, BLACK)

            # Show current player name
            player_text = font.render(f"Joueur: {self.player_name}", True, BLACK)
            change_name_text = font.render("Appuyez sur N pour Changer le Nom", True, BLACK)

            title_x = WIDTH // 2 - title_text.get_width() // 2
            title_y = HEIGHT // 2 - 200
            start_x = WIDTH // 2 - start_text.get_width() // 2
            start_y = HEIGHT // 2
            quit_x = WIDTH // 2 - quit_text.get_width() // 2
            quit_y = HEIGHT // 2 + 50
            settings_x = WIDTH // 2 - settings_text.get_width() // 2
            settings_y = HEIGHT // 2 + 100
            player_x = WIDTH // 2 - player_text.get_width() // 2
            player_y = HEIGHT // 2 - 100
            change_name_x = WIDTH // 2 - change_name_text.get_width() // 2
            change_name_y = HEIGHT // 2 - 50

            # Function to draw text with border
            def draw_text_with_border(text, x, y):
                border_color = (255, 255, 255)  # White border color
                screen.blit(font.render(text, True, border_color), (x - 2, y - 2))
                screen.blit(font.render(text, True, border_color), (x + 2, y - 2))
                screen.blit(font.render(text, True, border_color), (x - 2, y + 2))
                screen.blit(font.render(text, True, border_color), (x + 2, y + 2))
                screen.blit(font.render(text, True, BLACK), (x, y))  # Main text

            draw_text_with_border("Menu Principal", title_x, title_y)
            draw_text_with_border(f"Joueur: {self.player_name}", player_x, player_y)
            draw_text_with_border("Appuyez sur N pour Changer le Nom", change_name_x, change_name_y)
            draw_text_with_border("Appuyez sur S pour Commencer", start_x, start_y)
            draw_text_with_border("Appuyez sur Q pour Quitter", quit_x, quit_y)
            draw_text_with_border("Appuyez sur T pour les Paramètres", settings_x, settings_y)

            difficulty_selector.draw(screen)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    menu_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        self.player_name = self.get_player_name()
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
                    if change_name_x <= mouse_pos[
                        0] <= change_name_x + change_name_text.get_width() and change_name_y <= mouse_pos[
                        1] <= change_name_y + change_name_text.get_height():
                        self.player_name = self.get_player_name()

    def generate_obstacle(self):
        if len(self.obstacles) >= MAX_OBSTACLES:
            return  # Do not generate more obstacles if the limit is reached

        # Count current traps and non-traps
        current_traps = sum(1 for obs in self.obstacles if obs.is_trap)
        current_regular = sum(1 for obs in self.obstacles if not obs.is_trap)

        # Force generation of regular obstacles if there are too few
        force_regular = current_regular < 5 or current_traps > current_regular * 2

        # Determine if this should be a trap based on ratio and forcing
        is_trap = random.random() < TAUX_PIEGES and not force_regular


        if is_trap and current_traps >= MAX_OBSTACLES // 3:
            is_trap = False  # Convert to regular if too many traps
        elif not is_trap and current_regular >= MAX_BLACK_SQUARES:
            return


        if is_trap:
            available_keys = [key for key in self.available_keys
                              if key not in [obs.key for obs in self.obstacles]]
        else:
            available_keys = [key for key in self.available_keys
                              if key not in [obs.key for obs in self.obstacles]]

        if not available_keys:
            # Reset available keys if none left
            self.available_keys = AVAILABLE_KEYS.copy()
            available_keys = self.available_keys

        # Select a key and create the obstacle
        key = random.choice(available_keys)
        self.available_keys.remove(key)
        self.obstacles.append(Obstacle(WIDTH, is_trap, key,
                                       self.obstacle_size, self.difficulty.obstacle_speed))

    def reset_game(self):
        """Completely reset the game state for a new game"""
        self.update_high_scores()  # Save current score
        self.player = Player(WIDTH, HEIGHT)  # Reset player position
        self.obstacles.clear()  # Clear all obstacles
        self.score = 0
        self.lives = NB_VIES
        self.available_keys = AVAILABLE_KEYS.copy()
        self.rock_image = None
        self.rock_display_time = 0
        self.game_over = False

        # Reset lava
        self.lava = Lava(WIDTH, HEIGHT, LAVA_SPEED, "./ressources/lava.jpg")

        # Reset difficulty settings
        self.difficulty = self.load_difficulty(self.settings.settings['difficulty'])
        self.spawn_rate = self.get_initial_spawn_rate()

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

        current_difficulty = self.settings.settings['difficulty']

        # Find best score for current difficulty
        filtered_scores = [s for s in self.high_scores if
                           isinstance(s, dict) and
                           s.get('difficulty', current_difficulty) == current_difficulty]

        if filtered_scores:
            top_score = filtered_scores[0]
            high_score_text = font.render(
                f"Meilleur score ({current_difficulty}): {top_score['score']} par {top_score['name']}",
                True, BLACK)
        else:
            high_score_text = font.render(f"Pas encore de score pour {current_difficulty}", True, BLACK)

        # Also show overall best score regardless of difficulty
        if self.high_scores and isinstance(self.high_scores[0], dict):
            overall_best = self.high_scores[0]
            overall_difficulty = overall_best.get('difficulty', 'unknown')
            overall_text = font.render(
                f"Record absolu: {overall_best['score']} par {overall_best['name']} ({overall_difficulty})",
                True, BLACK)
            screen.blit(overall_text, (WIDTH // 2 - overall_text.get_width() // 2, HEIGHT // 2 - 25))

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
            self.reset_game()
            self.show_menu()
            self.death_animation = None

            # Load death sound
            death_sound = pygame.mixer.Sound('./ressources/death.mp3')
            death_sound_played = False

            while self.running:
                screen.fill(WHITE)

                if self.death_animation and not self.death_animation.done:
                    # Update and draw death animation
                    self.death_animation.update()
                    self.death_animation.draw(screen)

                    # Play death sound once when animation starts
                    if not death_sound_played:
                        death_sound.play()
                        death_sound_played = True

                    # Handle events during animation
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_r:
                                self.reset_game()
                                self.death_animation = None
                                death_sound_played = False
                            if event.key == pygame.K_m:
                                self.show_menu()
                                self.reset_game()
                                self.death_animation = None
                                death_sound_played = False

                elif not self.game_over:
                    # Normal game logic
                    self.background.draw(screen)
                    self.adjust_difficulty()

                    # Only generate new obstacles if not game over
                    if random.randint(0, self.spawn_rate) == 0:
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

                    lives_text = font.render(f"Vies: {self.lives}", True, BLACK)
                    screen.blit(lives_text, (20, 60))

                    if self.player.rect.bottom > self.lava.rect.top:
                        # Player touched lava - start lava death animation
                        from model.Animation import Animation
                        self.death_animation = Animation('./ressources/lavaloose.gif', WIDTH, HEIGHT)
                        self.game_over = True
                        death_sound_played = False  # Reset flag for new death

                    # Check if lives are depleted
                    if self.lives <= 0 and not self.game_over:
                        self.game_over = True
                        death_sound.play()  # Play death sound when lives are depleted

                    self.log_positions()
                    self.display_positions(screen)

                    # Increase lava speed based on score or time
                    if self.score % 100 == 0 and self.score != 0:
                        self.lava.increase_speed(self.difficulty.lava_speed_increment)

                else:
                    # Only show game over screen if animation is complete or not playing
                    if not self.death_animation or self.death_animation.done:
                        self.display_game_over()

                        # Play death sound if animation is not used (e.g., when lives run out)
                        if not self.death_animation and not death_sound_played:
                            death_sound.play()
                            death_sound_played = True

                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.running = False
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_r:
                                    self.reset_game()
                                    death_sound_played = False
                                if event.key == pygame.K_m:
                                    self.show_menu()
                                    self.reset_game()
                                    death_sound_played = False

                pygame.display.flip()
                self.clock.tick(30)  # Increased frame rate for smoother animation
        except KeyboardInterrupt:
            print("Game interrupted by user.")
        finally:
            pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()