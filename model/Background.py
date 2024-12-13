# model/Background.py
import pygame

class Background:
    def __init__(self, image_path, window_width, window_height):
        self.original_image = pygame.image.load(image_path)
        self.image1 = pygame.transform.scale(self.original_image.copy(), (window_width, window_height))
        self.image2 = pygame.transform.scale(self.original_image.copy(), (window_width, window_height))

        self.rect1 = self.image1.get_rect()
        self.rect2 = self.image2.get_rect()

        self.rect1.topleft = (0, 0)
        self.rect2.topleft = (0, -window_height)

    def move(self, player_rect, window_height):
        if player_rect.centery < window_height // 2:
            offset = window_height // 2 - player_rect.centery
            self.rect1.y += offset
            self.rect2.y += offset
            player_rect.centery = window_height // 2

        if self.rect1.top >= self.rect1.height:
            self.rect1.bottom = self.rect2.top

        if self.rect2.top >= self.rect2.height:
            self.rect2.bottom = self.rect1.top

    def draw(self, screen):
        screen.blit(self.image1, self.rect1)
        screen.blit(self.image2, self.rect2)