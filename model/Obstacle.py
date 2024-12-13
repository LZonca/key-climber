import pygame
import random

AVAILABLE_KEYS = ["A", "S", "D", "W", "Z", "Q", "E", "R", "T", "Y", "U", "I", "O", "P", "F", "G", "H", "J", "K", "L", "X", "C", "V", "B", "N", "M"]

class Obstacle:
    def __init__(self, window_width, is_trap=False, key=None):
        self.is_trap = is_trap
        self.color = (255, 0, 0) if self.is_trap else (0, 0, 0)
        self.size = 70
        self.speed = 10
        self.pos = [random.randint(0, window_width - self.size), 0]
        self.key = key if key else random.choice(AVAILABLE_KEYS)

    def move_down(self):
        self.pos[1] += self.speed

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, (*self.pos, self.size, self.size))

        font_size = int(self.size * 0.75)
        key_font = pygame.font.Font(None, font_size)
        key_text = key_font.render(self.key, True, (255, 255, 255))

        text_rect = key_text.get_rect(center=(self.pos[0] + self.size // 2, self.pos[1] + self.size // 2))
        screen.blit(key_text, text_rect)