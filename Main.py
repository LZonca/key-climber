import os
import time

import pygame
import random
import threading
import json
import math

from model.Difficulty import Difficulty
from model.DifficultySelector import DifficultySelector
from model.Slider import Slider
from model.Background import Background
from model.Lava import Lava
from model.Player import Player
from model.Obstacle import Obstacle
from model.Settings import Settings
from model.InputBox import  InputBox
from scores_api import ScoreAPI

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
pygame.display.set_caption("KeyScale")

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
    faster_sound.set_volume(game.settings.settings['sound_effects_volume'])
    faster_sound.play()

def play_wrong_key_sound():
    wrong_key_sound.set_volume(game.settings.settings['sound_effects_volume'])
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
        self.lava = Lava(WIDTH, HEIGHT, self.difficulty.lava_speed, "./ressources/lava.jpg")
        self.apply_settings()
        self.spawn_rate = self.get_initial_spawn_rate()
        self.background_image = pygame.image.load('./ressources/menu.jpg')
        self.background_image = pygame.transform.scale(self.background_image, (WIDTH, HEIGHT))
        self.player_name = "Anonymous"  # Default player name
        self.score_api = ScoreAPI("https://keyscale.lzonca.fr/api")
        try:
            icon = pygame.image.load('./ressources/menu.jpg')
            pygame.display.set_icon(icon)
        except Exception as e:
            print(f"Error loading application icon: {e}")

    def play_menu_music(self):
        """Plays a random menu music that's different from the last one played"""
        # Stop any currently playing music
        pygame.mixer.music.stop()

        # List of available menu music files
        menu_music_options = ['./ressources/menu_musique1.mp3', './ressources/menu_musique2.mp3']

        # Choose a music that's different from the last one
        if self.menu_music_history in menu_music_options and len(menu_music_options) > 1:
            menu_music_options.remove(self.menu_music_history)

        # Select from remaining options
        selected_music = random.choice(menu_music_options)
        self.menu_music_history = selected_music

        # Play the selected music with menu music volume
        pygame.mixer.music.load(selected_music)
        pygame.mixer.music.set_volume(self.settings.settings['menu_music_volume'])
        pygame.mixer.music.play(-1)  # Loop indefinitely

    def play_sound_effect(self, sound):
        """Play a sound effect with the proper volume setting"""
        sound.set_volume(self.settings.settings['sound_effects_volume'])
        sound.play()

    def play_game_music(self):
        """Switches to game music"""
        pygame.mixer.music.stop()
        pygame.mixer.music.load('./ressources/musique.mp3')
        pygame.mixer.music.set_volume(self.settings.settings['game_music_volume'])
        pygame.mixer.music.play(-1)  # Loop indefinitely

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
            # First attempt to save score to the API
            if self.score > 0:  # Only send scores greater than 0
                api_success = self.score_api.save_game_score(
                    name=self.player_name,
                    score=self.score,
                    difficulty=self.settings.settings['difficulty']
                )

                if api_success:
                    # If API save was successful, get updated scores from API
                    try:
                        self.high_scores = self.score_api.get_game_scores()
                        print("Scores successfully retrieved from API")
                        return self.high_scores
                    except Exception as e:
                        print(f"Couldn't retrieve scores from API: {e}")
                        # Continue to local file method as fallback

            # Fallback to local file if API failed or score was 0
            if not os.path.exists(self.scores_file):
                with open(self.scores_file, 'w') as file:
                    json.dump([], file)

            with open(self.scores_file, 'r') as file:
                scores = json.load(file)

            if self.score > 0:
                new_entry = {
                    "name": self.player_name,
                    "score": self.score,
                    "difficulty": self.settings.settings['difficulty']
                }
                scores.append(new_entry)

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

    def load_scores(self):
        """Load scores from API with fallback to local file"""
        try:
            # Try to load from API first
            try:
                api_scores = self.score_api.get_game_scores()
                if api_scores:
                    print("Scores loaded from API")
                    return api_scores
            except Exception as e:
                print(f"Failed to load scores from API: {e}")
                print("Falling back to local scores")

            # Fallback to local file
            if os.path.exists(self.scores_file):
                with open(self.scores_file, 'r') as file:
                    scores = json.load(file)
                    return scores
            return []
        except Exception as e:
            print(f"Error loading scores: {e}")
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
            'facile': Difficulty(
                'facile',
                obstacle_speed=2,
                spawn_rate=50,  # Make letters appear more frequently on easy
                lava_speed_increment=0.03,
                lava_start_delay=10.0,  # 8 seconds delay before lava starts moving
                initial_obstacles=10,  # Spawn 10 obstacles at the start
                lava_speed=0.3  # Slower lava speed for easy difficulty
            ),
            'moyen': Difficulty(
                'moyen',
                obstacle_speed=4,
                spawn_rate=50,
                lava_speed_increment=0.07,
                lava_start_delay=5.0,  # 5 seconds delay
                initial_obstacles=8,
                lava_speed=0.5  # Medium lava speed
            ),
            'difficile': Difficulty(
                'difficile',
                obstacle_speed=6,
                spawn_rate=30,
                lava_speed_increment=0.15,
                lava_start_delay=2.0,  # 2 seconds delay
                initial_obstacles=5,
                lava_speed=0.8  # Faster lava speed for hard difficulty
            )
        }
        return difficulties.get(difficulty_name, difficulties['moyen'])

    def apply_settings(self):
        """Apply settings from the settings object"""
        # Apply display settings
        if self.settings.settings['display_mode'] == 'fullscreen':
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        # Apply font size to obstacles text
        global obstacle_font
        obstacle_font = pygame.font.Font(None, int(self.settings.settings['font_size']))

        # Apply square size to obstacles
        self.obstacle_size = int(self.settings.settings['square_size'])

        # Apply spawn rate from settings
        self.spawn_rate = int(self.settings.settings.get('spawn_rate', BLACK_SQUARE_SPAWN_RATE))

        # Apply correct volume based on what's currently playing
        if pygame.mixer.music.get_busy():
            # Check if we're in menu or game
            if hasattr(self, 'menu_music_history') and self.menu_music_history and \
                    ('menu_musique' in self.menu_music_history):
                # Menu music is playing
                pygame.mixer.music.set_volume(self.settings.settings['menu_music_volume'])
            else:
                # Game music is playing
                pygame.mixer.music.set_volume(self.settings.settings['game_music_volume'])

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
        self.play_menu_music()
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
                        self.play_game_music()
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
                        self.play_game_music()  # Switch to game music
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

    # Add this to your adjust_difficulty method or wherever you handle lava speed
    def adjust_lava_speed(self):
        # Increase lava speed based on score and difficulty
        base_lava_speed = 0.5  # Default speed
        score_factor = self.score / 100  # Speed increases with score

        # Apply difficulty multiplier
        difficulty_multiplier = self.difficulty.lava_speed_increment

        # Calculate new lava speed
        new_speed = base_lava_speed + (score_factor * difficulty_multiplier)

        # Cap the maximum speed to prevent impossibility
        max_speed = 3.0
        new_speed = min(new_speed, max_speed)

        # Update lava speed
        self.lava.speed = new_speed

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

    def create_tutorial(self):
        """Create tutorial letters spelling 'TYPE!'"""
        tutorial_word = "APPUYER!"
        letter_width = self.obstacle_size
        total_width = len(tutorial_word) * letter_width * 1.5  # 1.5 for spacing
        start_x = (WIDTH - total_width) // 2

        for i, letter in enumerate(tutorial_word):
            obstacle = Obstacle(WIDTH, False, letter, self.obstacle_size, 0)  # Speed 0 = static
            obstacle.pos = [start_x + i * letter_width * 1.5, HEIGHT // 3]  # Position in upper third
            obstacle.tutorial = True  # Mark as tutorial letter
            self.tutorial_letters.append(obstacle)

    def handle_tutorial_key_press(self, key):
        """Handle key presses during tutorial"""
        for obstacle in self.tutorial_letters[:]:  # Use slice to avoid modification during iteration
            if key == obstacle.key:
                # Remove the letter and check if tutorial is complete
                self.tutorial_letters.remove(obstacle)

                # Play climb sound effect
                self.player.climb()

                if not self.tutorial_letters:
                    # All tutorial letters cleared
                    self.tutorial_completed = True
                    self.countdown_start_time = pygame.time.get_ticks()
                    self.countdown_active = True
                return

    def draw_countdown(self, screen):
        """Draw countdown after tutorial completion"""
        if not self.countdown_active:
            return

        elapsed = (pygame.time.get_ticks() - self.countdown_start_time) // 1000
        remaining = 3 - elapsed

        if remaining <= 0:
            self.countdown_active = False
            self.tutorial_active = False
            return

        countdown_font = pygame.font.Font(None, 150)
        countdown_text = countdown_font.render(str(remaining), True, RED)

        screen.blit(countdown_text,
                    (WIDTH // 2 - countdown_text.get_width() // 2,
                     self.player.rect.bottom + 100))

    def reset_game(self):
        """Completely reset the game state for a new game"""
        self.update_high_scores()
        self.player = Player(WIDTH, HEIGHT)
        self.obstacles.clear()
        self.score = 0
        self.previous_score = 0
        self.lives = NB_VIES
        self.available_keys = AVAILABLE_KEYS.copy()
        self.rock_image = None
        self.rock_display_time = 0
        self.game_over = False
        self.death_animation = None

        self.tutorial_active = True
        self.tutorial_letters = []
        self.tutorial_completed = False
        self.countdown_start_time = 0
        self.countdown_active = False

        self.difficulty = self.load_difficulty(self.settings.settings['difficulty'])
        self.spawn_rate = self.get_initial_spawn_rate()

        # Reset lava with the appropriate delay and speed from difficulty
        self.lava = Lava(WIDTH, HEIGHT, self.difficulty.lava_speed, "./ressources/lava.jpg")
        self.lava.set_start_delay(self.difficulty.lava_start_delay)

        # Create tutorial letters
        self.create_tutorial()

        # Initialize menu music history if not already set
        if not hasattr(self, 'menu_music_history'):
            self.menu_music_history = None

    def spawn_initial_obstacles(self):
        """Spawn a batch of initial obstacles based on difficulty setting"""
        for _ in range(self.difficulty.initial_obstacles):
            self.generate_obstacle()

            # Spread the obstacles vertically
            if self.obstacles:
                last_obstacle = self.obstacles[-1]
                last_obstacle.pos[1] = random.randint(100, HEIGHT // 2)  # Place in upper half of screen

    def draw_lava_countdown(self, screen):
        if not self.lava.moving_enabled:
            remaining = max(0, (self.lava.start_delay - (pygame.time.get_ticks() - self.lava.start_time)) / 1000)
            countdown_text = font.render(f"Lava starts in: {remaining:.1f}s", True, RED)
            screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT - 50))

    def handle_key_press(self, key):
        for obstacle in self.obstacles:
            if key == obstacle.key:
                if obstacle.is_trap:
                    # Trap handling code (unchanged)
                    sound_thread = threading.Thread(target=lambda: self.play_sound_effect(wrong_key_sound))
                    sound_thread.start()
                    rock_thread = threading.Thread(target=self.display_rock_image)
                    rock_thread.start()
                    self.lives -= 1
                else:
                    self.score += 10
                    self.player.climb()
                    self.background.move(self.player.rect, HEIGHT)

                    # Use the lava's move_down method which is properly implemented
                    down_amount = 100  # Adjust this value as needed
                    self.lava.move_down(down_amount)

                    # Ensure lava speed is properly adjusted
                    self.adjust_lava_speed()

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
            pause_text = font.render("Pause", True, (255, 255, 255))
            resume_text = font.render("Appuyer sur ESC pour reprendre", True, (255, 255, 255))
            main_menu_text = font.render("Appuyer sur M pour retourner au menu principal", True, (255, 255, 255))
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
            # Load the image
            temp_image = pygame.image.load(rock_image_path)

            # Create a new surface and scale it
            self.rock_image = pygame.transform.scale(temp_image, (WIDTH, HEIGHT))

            # Ensure the surface is not locked
            if self.rock_image.get_locked():
                self.rock_image.unlock()

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

        # Check if this is a new best score for the current difficulty
        is_new_best_score = False
        filtered_scores = [s for s in self.high_scores if
                           isinstance(s, dict) and
                           s.get('difficulty', current_difficulty) == current_difficulty]

        if not filtered_scores or self.score > filtered_scores[0]['score']:
            is_new_best_score = True

        # Display information based on current scores
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

        # Display the new best score message with animation effect
        if is_new_best_score and self.score > 0:
            # Create pulsing text effect using sine wave
            pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5  # 0.0 to 1.0
            size_factor = 1.0 + pulse * 0.3  # Pulse between 1.0x and 1.3x

            new_best_font = pygame.font.Font(None, int(72 * size_factor))
            new_best_text = new_best_font.render("NOUVEAU RECORD!", True, (255, 215, 0))  # Gold color

            # Add glowing effect by drawing the text multiple times with different colors
            for offset in range(3, 0, -1):
                glow_surface = new_best_font.render("NOUVEAU RECORD!", True, (255, 215, 0, 100))
                screen.blit(glow_surface,
                            (WIDTH // 2 - glow_surface.get_width() // 2,
                             HEIGHT // 2 - 200 - offset * 2))

            screen.blit(new_best_text,
                        (WIDTH // 2 - new_best_text.get_width() // 2,
                         HEIGHT // 2 - 200))

        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(user_score_text, (WIDTH // 2 - user_score_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()

    def show_settings_menu(self):
        # Create individual sliders for the three audio channels
        menu_music_slider = Slider(WIDTH // 2 - 100, HEIGHT // 2 - 150, 200, 20,
                                   0.0, 1.0, self.settings.settings['menu_music_volume'])
        game_music_slider = Slider(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 20,
                                   0.0, 1.0, self.settings.settings['game_music_volume'])
        sound_effects_slider = Slider(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 20,
                                      0.0, 1.0, self.settings.settings['sound_effects_volume'])

        # Original sliders for font and square size
        font_size_slider = Slider(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 20,
                                  10, 100, self.settings.settings['font_size'])
        square_size_slider = Slider(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 20,
                                    10, 100, self.settings.settings['square_size'])

        settings_running = True
        while settings_running:
            screen.blit(self.background_image, (0, 0))  # Draw the background image
            title_text = font.render("Paramètres", True, BLACK)
            back_text = font.render("Appuyer sur B pour retourner à l'écran précédent", True, BLACK)
            validate_text = font.render("Appuyer sur V pour confirmer", True, BLACK)

            title_x = WIDTH // 2 - title_text.get_width() // 2
            title_y = HEIGHT // 2 - 300
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

            draw_text_with_border("Paramètres", title_x, title_y)
            draw_text_with_border("Appuyer sur B pour retourner à l'écran précédent", back_x, back_y)
            draw_text_with_border("Appuyer sur V pour confirmer", validate_x, validate_y)

            # Draw all sliders
            menu_music_slider.draw(screen)
            game_music_slider.draw(screen)
            sound_effects_slider.draw(screen)
            font_size_slider.draw(screen)
            square_size_slider.draw(screen)

            # Draw slider labels
            menu_music_label = font.render(f"Musique du menu: {int(menu_music_slider.value * 100)}%", True, BLACK)
            game_music_label = font.render(f"Musique du jeu: {int(game_music_slider.value * 100)}%", True, BLACK)
            sound_effects_label = font.render(f"Effets sonores: {int(sound_effects_slider.value * 100)}%", True, BLACK)
            font_size_label = font.render(f"Taille de la police: {int(font_size_slider.value)}", True, BLACK)
            square_size_label = font.render(f"Taille des obstacles: {int(square_size_slider.value)}", True, BLACK)

            # Position labels
            screen.blit(menu_music_label, (menu_music_slider.rect.x, menu_music_slider.rect.y - 30))
            screen.blit(game_music_label, (game_music_slider.rect.x, game_music_slider.rect.y - 30))
            screen.blit(sound_effects_label, (sound_effects_slider.rect.x, sound_effects_slider.rect.y - 30))
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
                        # Save all volume settings
                        self.settings.settings['menu_music_volume'] = menu_music_slider.value
                        self.settings.settings['game_music_volume'] = game_music_slider.value
                        self.settings.settings['sound_effects_volume'] = sound_effects_slider.value

                        # Legacy volume setting (for compatibility)
                        self.settings.settings['volume'] = menu_music_slider.value

                        # Save other settings
                        self.settings.settings['font_size'] = font_size_slider.value
                        self.settings.settings['square_size'] = square_size_slider.value
                        self.settings.save_settings()
                        self.apply_settings()  # Apply the new settings
                        print(
                            f"Settings applied: Menu Music={menu_music_slider.value}, Game Music={game_music_slider.value}, "
                            f"Sound Effects={sound_effects_slider.value}, Font Size={font_size_slider.value}, "
                            f"Square Size={square_size_slider.value}")
                        settings_running = False

                # Handle all slider events
                menu_music_slider.handle_event(event)
                game_music_slider.handle_event(event)
                sound_effects_slider.handle_event(event)
                font_size_slider.handle_event(event)
                square_size_slider.handle_event(event)

                # Apply menu music volume immediately for feedback
                if event.type == pygame.MOUSEBUTTONUP:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.set_volume(menu_music_slider.value)

    def run(self):
        try:
            self.reset_game()
            self.menu_music_history = None
            self.play_menu_music()
            self.show_menu()
            self.death_animation = None

            while self.running:
                screen.fill(WHITE)


                if self.death_animation and not self.death_animation.done:

                    self.death_animation.update()
                    self.death_animation.draw(screen)

                    # Handle events during animation
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_r:
                                self.reset_game()
                                self.death_animation = None
                            if event.key == pygame.K_m:
                                self.show_menu()
                                self.reset_game()
                                self.death_animation = None

                elif not self.game_over:
                    # Normal game logic
                    self.background.draw(screen)

                    if self.tutorial_active:
                        # Tutorial code (unchanged)
                        for obstacle in self.tutorial_letters:
                            obstacle.draw(screen, font)

                        instruction_font = pygame.font.Font(None, 48)
                        instruction_text = instruction_font.render("Appuyez sur les lettres pour démarrer !", True, BLACK)
                        screen.blit(instruction_text,
                                    (WIDTH // 2 - instruction_text.get_width() // 2,
                                     HEIGHT // 2 - 100))

                        if self.countdown_active:
                            self.draw_countdown(screen)

                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.running = False
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_ESCAPE:
                                    self.pause_menu()
                                else:
                                    letter = pygame.key.name(event.key).upper()
                                    self.handle_tutorial_key_press(letter)

                    else:
                        self.adjust_difficulty()
                        self.adjust_lava_speed()

                        if random.randint(0, self.spawn_rate) == 0:
                            self.generate_obstacle()

                        for obstacle in self.obstacles[:]:
                            obstacle.move_down()
                            if obstacle.pos[1] > HEIGHT:
                                self.obstacles.remove(obstacle)
                                print(f"Missed letter - lives remaining: {self.lives}")


                                if obstacle.pos[1] > self.lava.rect.top:
                                    self.lava.speed_up(self.difficulty.lava_speed_increment)

                                if self.lives <= 0:
                                    print("Game over: No lives remaining (missed too many letters)")
                                    self.game_over = True
                                    self.start_death_animation('rock_loose.gif')
                            obstacle.draw(screen, font)

                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.running = False
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_ESCAPE:
                                    self.pause_menu()
                                else:
                                    letter = pygame.key.name(event.key).upper()
                                    self.handle_key_press(letter)

                        self.player.draw(screen)
                        self.lava.update_position()
                        self.lava.draw(screen)

                        if not self.lava.moving_enabled:
                            self.draw_lava_countdown(screen)

                        self.background.move(self.player.rect, HEIGHT)

                        if self.rock_image and time.time() < self.rock_display_time:
                            screen.blit(self.rock_image, (
                                WIDTH // 2 - self.rock_image.get_width() // 2,
                                HEIGHT // 2 - self.rock_image.get_height() // 2))
                        else:
                            self.rock_image = None

                        score_text = font.render(f"Score: {self.score}", True, BLACK)
                        screen.blit(score_text, (20, 20))

                        lives_text = font.render(f"Vies: {self.lives}", True, BLACK)
                        screen.blit(lives_text, (20, 60))

                        difficulty_text = font.render(f"Difficulté: {self.difficulty.name}", True, BLACK)
                        screen.blit(difficulty_text, (20, 100))

                        # Check if player has touched lava
                        if self.player.rect.bottom > self.lava.rect.top:
                            print("Game over: Player touched lava")
                            self.game_over = True
                            self.start_death_animation('lavaloose.gif')

                else:
                    if not self.death_animation or self.death_animation.done:
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
                self.clock.tick(45)
        except KeyboardInterrupt:
            print("Game interrupted by user.")
        except Exception as e:
            print(f"Game crashed with error: {e}")
        finally:
            pygame.quit()

    def start_death_animation(self, animation_file):
        """Start death animation with synchronized sound after small delay"""
        from model.Animation import Animation
        import threading

        # Create and initialize the animation
        animation_path = f'./ressources/{animation_file}'
        print(f"Loading death animation: {animation_path}")

        # Create the animation
        self.death_animation = Animation(animation_path, WIDTH, HEIGHT,
                                         skip_fade_in=('lava' not in animation_file))

        # Load sound immediately to avoid delays
        try:
            death_sound = pygame.mixer.Sound('./ressources/death.mp3')
            # Apply sound effects volume setting
            death_sound.set_volume(self.settings.settings['sound_effects_volume'])
        except Exception as e:
            print(f"Error loading death sound: {e}")
            return

        # Use a single approach to play the death sound
        # Remove the play_sound_with_delay function and thread

        def monitor_animation_and_play_sound():
            wait_start = time.time()
            while not self.death_animation.loading_complete and time.time() - wait_start < 2:
                time.sleep(0.05)

            if not self.death_animation.loading_complete:
                print("Animation loading timed out")
                return

            total_frames = len(self.death_animation.frames)
            if total_frames == 0:
                print("No animation frames loaded")
                return

            target_frame = int(total_frames * 0.5)
            print(f"Will play sound at frame {target_frame} of {total_frames}")

            last_frame = -1
            while not self.death_animation.done:
                current_frame = self.death_animation.current_frame

                # Only check when frame changes to reduce CPU usage
                if current_frame != last_frame:
                    last_frame = current_frame

                    # Debug information
                    if current_frame % 5 == 0:  # Only log every 5th frame
                        print(f"Animation at frame {current_frame}/{total_frames}")

                    # Play sound at target frame
                    if current_frame == target_frame:
                        print("Playing death sound")
                        death_sound.play()
                        break

                time.sleep(0.01)

        # Start the monitoring thread
        sound_thread = threading.Thread(target=monitor_animation_and_play_sound)
        sound_thread.daemon = True
        sound_thread.start()

        print(f"Death animation started: {animation_file}")

        def monitor_animation_and_play_sound():
            wait_start = time.time()
            while not self.death_animation.loading_complete and time.time() - wait_start < 2:
                time.sleep(0.05)

            if not self.death_animation.loading_complete:
                print("Animation loading timed out")
                return

            total_frames = len(self.death_animation.frames)
            if total_frames == 0:
                print("No animation frames loaded")
                return

            target_frame = int(total_frames * 0.5)
            print(f"Will play sound at frame {target_frame} of {total_frames}")

            last_frame = -1
            while not self.death_animation.done:
                current_frame = self.death_animation.current_frame

                # Only check when frame changes to reduce CPU usage
                if current_frame != last_frame:
                    last_frame = current_frame

                    # Debug information
                    if current_frame % 5 == 0:  # Only log every 5th frame
                        print(f"Animation at frame {current_frame}/{total_frames}")

                    # Play sound at target frame
                    if current_frame == target_frame:
                        print("Playing death sound")
                        death_sound.play()
                        break

                time.sleep(0.01)

        # Start the monitoring thread
        sound_thread = threading.Thread(target=monitor_animation_and_play_sound)
        sound_thread.daemon = True
        sound_thread.start()

if __name__ == "__main__":
    game = Game()
    game.run()