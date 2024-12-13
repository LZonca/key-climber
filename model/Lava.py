# model/Lava.py
import pygame

class Lava:
    def __init__(self, window_width, window_height, speed):
        self.image = pygame.image.load('./ressources/lava.jpg')
        self.image = pygame.transform.scale(self.image, (window_width, 50))  # Adjust the height as needed
        self.rect = self.image.get_rect()
        self.rect.bottom = window_height
        self.speed = speed

    def move_up(self, background_speed):
        self.rect.y -= background_speed * 0.05  # Reduce the speed multiplier

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)