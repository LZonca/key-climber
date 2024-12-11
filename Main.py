import time

import pygame
import random
import threading
from ressources.model.Player import Player
from ressources.model.Obstacle import Obstacle

# Global constant for available keys
AVAILABLE_KEYS = ["A", "S", "D", "W", "Z", "Q"]
MAX_ROCK_IMG=4
TAUX_PIEGES=0.1
NB_VIES=3
MAX_BLACK_SQUARES = 10
BLACK_SQUARE_SPAWN_RATE = 20

# Initialisation de Pygame
pygame.init()

# Fenêtre de jeu
WIDTH, HEIGHT = 400, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jeu d'Escalade")

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Police
font = pygame.font.Font(None, 36)

# Charger le son
wrong_key_sound = pygame.mixer.Sound('./ressources/wrong_key.mp3')
faster_sound = pygame.mixer.Sound('./ressources/faster.wav')
# Thread pour la musique
def play_music():
    pygame.mixer.music.load('C:/Users/leozo/PycharmProjects/JeuLicence/ressources/musique.mp3')
    pygame.mixer.music.play(-1)

music_thread = threading.Thread(target=play_music)
music_thread.start()

def play_faster_sound():
    faster_sound.play()

# Fonction pour jouer le son de la mauvaise touche
def play_wrong_key_sound():
    wrong_key_sound.play()

class Game:
    def __init__(self):
        self.player = Player()
        self.obstacles = []
        self.score = 0
        self.lives = NB_VIES
        self.clock = pygame.time.Clock()
        self.running = True
        self.available_keys = AVAILABLE_KEYS.copy()
        self.rock_image = None
        self.game_over = False

    def reset_game(self):
        self.player = Player()
        self.obstacles = []
        self.score = 0
        self.lives = NB_VIES
        self.available_keys = AVAILABLE_KEYS.copy()
        self.rock_image = None
        self.game_over = False

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
        self.obstacles.append(Obstacle(is_trap, key))

    def handle_key_press(self, key):
        for obstacle in self.obstacles:
            if key == obstacle.key:
                if obstacle.is_trap:
                    self.lives -= 1
                    sound_thread = threading.Thread(target=play_wrong_key_sound)
                    sound_thread.start()
                    rock_thread = threading.Thread(target=self.display_rock_image)
                    rock_thread.start()
                    if self.lives == 0:
                        self.game_over = True
                else:
                    self.score += 10
                    self.player.next_frame()
                self.obstacles.remove(obstacle)
                return

    def display_rock_image(self):
        rock_number = random.randint(1, MAX_ROCK_IMG)
        rock_image_path = f'./ressources/rocks/rock{rock_number}.jpeg'
        self.rock_image = pygame.image.load(rock_image_path)
        self.rock_display_time = time.time() + 1

    def display_game_over(self):
        game_over_text = font.render("Game Over", True, RED)
        restart_text = font.render("Press R to Restart", True, RED)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - game_over_text.get_height() // 2))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50 - restart_text.get_height() // 2))
        pygame.display.flip()

    def run(self):
        while self.running:
            screen.fill(WHITE)

            if not self.game_over:
                if random.randint(1, BLACK_SQUARE_SPAWN_RATE) == 1:
                    self.generate_obstacle()

                for obstacle in self.obstacles:
                    obstacle.move_down()
                    if obstacle.pos[1] > HEIGHT:
                        if not obstacle.is_trap:
                            sound_thread = threading.Thread(target=play_faster_sound())
                            sound_thread.start()
                        self.obstacles.remove(obstacle)
                    obstacle.draw(screen, font)

                self.player.draw(screen)

                if self.rock_image and time.time() < self.rock_display_time:
                    screen.blit(self.rock_image, (
                        WIDTH // 2 - self.rock_image.get_width() // 2, HEIGHT // 2 - self.rock_image.get_height() // 2))
                else:
                    self.rock_image = None

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.KEYDOWN:
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
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                        self.reset_game()

            pygame.display.flip()
            self.clock.tick(20)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()