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
        self.rect.centerx = window_width // 2
        self.rect.centery = window_height // 2  # Center the player vertically

        self.climbing_speed = 5  # Adjust the speed value

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def next_frame(self):
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.image = self.images[self.current_image_index]

    def climb(self):
        self.rect.y = max(0, self.rect.y - self.climbing_speed)
        self.next_frame()

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy