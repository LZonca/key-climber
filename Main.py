import os
import time

import pygame
import random
import threading
import json
from model.Background import Background
from model.Player import Player
from model.Obstacle import Obstacle

os.environ['SDL_VIDEO_CENTERED'] = '1'

# Global constant for available keys
AVAILABLE_KEYS = ["A", "S", "D", "W", "Z", "Q", "E", "R", "T", "Y", "U", "I", "O", "P", "F", "G", "H", "J", "K", "L", "X", "C", "V", "B", "N", "M"]
MAX_ROCK_IMG = 4
TAUX_PIEGES = 0.15
NB_VIES = 4
MAX_BLACK_SQUARES = 20
BLACK_SQUARE_SPAWN_RATE = 15

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
        self.player = Player(WIDTH, HEIGHT)
        self.obstacles = []
        self.score = 0
        self.lives = NB_VIES
        self.clock = pygame.time.Clock()
        self.running = True
        self.available_keys = AVAILABLE_KEYS.copy()
        self.rock_image = None
        self.game_over = False
        self.background = Background('./ressources/background.jpg', 5, WIDTH, HEIGHT)
        self.scores_file = './scores.json'
        self.high_scores = self.load_scores()

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

    def update_high_scores(self):
        self.high_scores.append(self.score)
        self.high_scores = sorted(self.high_scores, reverse=True)[:10]  # Keep top 10 scores
        self.save_scores()

    def show_menu(self):
        self.reset_game()  # Reset the game state before showing the menu
        menu_running = True
        while menu_running:
            screen.fill(WHITE)
            title_text = font.render("Jeu d'Escalade", True, BLACK)
            start_text = font.render("Press ENTER to Start", True, BLACK)

            title_x = WIDTH // 2 - title_text.get_width() // 2
            title_y = HEIGHT // 2 - 200
            start_x = WIDTH // 2 - start_text.get_width() // 2
            start_y = title_y + 150  # Adjusted to be below the title

            screen.blit(title_text, (title_x, title_y))
            screen.blit(start_text, (start_x, start_y))

            # Display high scores
            score_title_text = font.render("High Scores", True, BLACK)
            score_title_x = WIDTH // 2 - score_title_text.get_width() // 2
            score_title_y = start_y + 100  # Adjusted to be below the start text
            screen.blit(score_title_text, (score_title_x, score_title_y))

            # Calculate spacing based on the number of high scores and available height
            max_scores_display = min(len(self.high_scores), 10)
            score_spacing = (HEIGHT - score_title_y - 100) // (max_scores_display + 1)

            for i, score in enumerate(self.high_scores[:max_scores_display]):
                score_text = font.render(f"{i + 1}. {score}", True, BLACK)
                score_x = WIDTH // 2 - score_text.get_width() // 2
                score_y = score_title_y + (i + 1) * score_spacing
                screen.blit(score_text, (score_x, score_y))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    menu_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        menu_running = False

    def generate_obstacle(self):
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
                key = random.choice(self.available_keys)
        else:
            if len([obs for obs in self.obstacles if not obs.is_trap]) >= MAX_BLACK_SQUARES:
                return
            key = random.choice(self.available_keys)
        self.obstacles.append(Obstacle(WIDTH, is_trap, key))

    def reset_game(self):
        self.update_high_scores()
        self.player = Player(WIDTH, HEIGHT)
        self.obstacles = []
        self.score = 0
        self.lives = NB_VIES
        self.available_keys = AVAILABLE_KEYS.copy()
        self.rock_image = None
        self.game_over = False

    def handle_key_press(self, key):
        for obstacle in self.obstacles:
            if key == obstacle.key:
                if obstacle.is_trap:
                    self.lives -= 1
                    sound_thread = threading.Thread(target=play_wrong_key_sound)
                    sound_thread.start()
                    rock_thread = threading.Thread(target=self.display_rock_image)
                    rock_thread.start()
                    if self.lives <= 0:
                        self.game_over = True
                else:
                    self.score += 10
                    self.player.next_frame()
                    self.background.move()
                self.obstacles.remove(obstacle)
                return

    def pause_menu(self):
        paused = True
        while paused:
            screen.fill(WHITE)
            pause_text = font.render("Paused", True, BLACK)
            resume_text = font.render("Press ESC to Resume", True, BLACK)
            main_menu_text = font.render("Press M for Main Menu", True, BLACK)
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
        game_over_text = font.render("Game Over", True, RED)
        restart_text = font.render("Press R to Restart", True, RED)
        menu_text = font.render("Press M for Main Menu", True, RED)
        user_score_text = font.render(f"Your Score: {self.score}", True, BLACK)
        high_score_text = font.render(f"Highest Score: {self.high_scores[0]}", True, BLACK)

        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
        screen.blit(user_score_text, (WIDTH // 2 - user_score_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()

    def run(self):
        try:
            self.show_menu()
            while self.running:
                screen.fill(WHITE)

                if not self.game_over:
                    self.background.draw(screen)

                    if random.randint(1, BLACK_SQUARE_SPAWN_RATE) == 1:
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