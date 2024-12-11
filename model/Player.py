import pygame

class Player:
    def __init__(self, window_width, window_height):
        self.images = [
            pygame.image.load('./ressources/climbing-man-1.png'),
            pygame.image.load('./ressources/climbing-man-2.png'),
        ]

        self.current_image_index = 0
        self.image = self.images[self.current_image_index]
        self.pos = [window_width // 2 - self.image.get_width() // 2, window_height - 100]
        self.size = self.image.get_size()
        self.speed = 40

    def draw(self, screen):
        screen.blit(self.image, self.pos)

    def next_frame(self):
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.image = self.images[self.current_image_index]