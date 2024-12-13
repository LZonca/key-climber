# model/Player.py
import pygame

class Player:
    def __init__(self, window_width, window_height):
        self.images = [
            pygame.image.load('./ressources/climbing-man-1.png'),
            pygame.image.load('./ressources/climbing-man-2.png'),
        ]

        self.current_image_index = 0
        self.image = self.images[self.current_image_index]
        self.rect = self.image.get_rect()
        self.rect.center = (window_width // 2, window_height - 150)  # Start higher up

        self.speed = 5  # Reduced speed value

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

    def next_frame(self):
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.image = self.images[self.current_image_index]
        self.rect = self.image.get_rect(center=self.rect.center)

    def move(self, dx, dy):
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed