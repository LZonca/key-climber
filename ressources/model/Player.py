import pygame

class Player:
    def __init__(self):
        self.images = [
            pygame.image.load('./ressources/climbing-man-1.png'),
            pygame.image.load('./ressources/climbing-man-2.png'),
        ]
        self.current_image_index = 0
        self.image = self.images[self.current_image_index]
        self.pos = [400 // 2, 800 - 100]
        self.size = self.image.get_size()
        self.speed = 5

    def move_up(self):
        self.pos[1] -= self.speed

    def draw(self, screen):
        screen.blit(self.image, self.pos)

    def next_frame(self):
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.image = self.images[self.current_image_index]