import pygame
import random

class Obstacle:
    def __init__(self, is_trap=False, key=None):
        self.is_trap = is_trap
        self.color = (255, 0, 0) if self.is_trap else (0, 0, 0)
        self.size = 50
        self.speed = 10
        self.pos = [random.randint(0, 400 - self.size), 0]
        self.key = key if key else random.choice(["A", "S", "D", "W", "Z", "Q"])

    def move_down(self):
        self.pos[1] += self.speed

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, (*self.pos, self.size, self.size))
        key_text = font.render(self.key, True, (255, 255, 255))
        screen.blit(key_text, (self.pos[0] + 10, self.pos[1] + 10))