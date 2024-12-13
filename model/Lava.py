import pygame

class Lava:
    def __init__(self, width, height, speed, image_path):
        self.rect = pygame.Rect(0, height - 50, width, 50)
        self.speed = speed
        self.moving_up = True
        self.target_position = self.rect.y
        self.image = pygame.image.load(image_path)
        self.original_image = self.image

    def update_position(self):
        if self.moving_up:
            self.rect.y -= self.speed
        else:
            if self.rect.y < self.target_position:
                self.rect.y += self.speed
            else:
                self.moving_up = True

    def move_down(self, amount):
        self.target_position = min(self.rect.y + amount, pygame.display.Info().current_h - 50)
        self.moving_up = False

    def increase_speed(self, increment):
        self.speed += increment

    def reset_position(self):
        self.rect.y = pygame.display.Info().current_h - 50
        self.target_position = self.rect.y

    def draw(self, screen):
        height = pygame.display.Info().current_h - self.rect.y
        scaled_image = pygame.transform.scale(self.original_image, (self.rect.width, height))
        screen.blit(scaled_image, (self.rect.x, self.rect.y))