import pygame

class Background:
    def __init__(self, image_path, speed, window_width, window_height):
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (window_width, window_height))
        self.speed = speed * 2
        self.y1 = 0
        self.y2 = -window_height

    def move(self):
        self.y1 += self.speed
        self.y2 += self.speed
        if self.y1 >= self.image.get_height():
            self.y1 = -self.image.get_height()
        if self.y2 >= self.image.get_height():
            self.y2 = -self.image.get_height()

    def draw(self, screen):
        screen.blit(self.image, (0, self.y1))
        screen.blit(self.image, (0, self.y2))