import pygame
import random

AVAILABLE_KEYS = ["A", "S", "D", "W", "Z", "Q", "E", "R", "T", "Y", "U", "I", "O", "P", "F", "G", "H", "J", "K", "L",
                  "X", "C", "V", "B", "N", "M"]


class Obstacle:
    def __init__(self, width, is_trap, key, size, speed=5):
        self.width = width
        self.is_trap = is_trap
        self.key = key
        self.size = size
        self.pos = [random.randint(0, width - size), -size]
        self.color = (255, 0, 0) if is_trap else (0, 0, 0)
        self.speed = speed
        self.speed = speed
        self.tutorial = False

        # Add a subtle border for traps to make them more distinguishable
        self.border_color = (139, 0, 0) if self.is_trap else (50, 50, 50)

    def move_down(self):
        if not self.tutorial and self.speed > 0:
            self.pos[1] += self.speed

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, (*self.pos, self.size, self.size))
        text = font.render(self.key, True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.pos[0] + self.size // 2, self.pos[1] + self.size // 2))
        screen.blit(text, text_rect)