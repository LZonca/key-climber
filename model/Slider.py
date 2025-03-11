import pygame

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.handle_rect = pygame.Rect(x, y, height, height)
        self.handle_rect.centerx = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        self.dragging = False

    def draw(self, screen):
        pygame.draw.rect(screen, (200, 200, 200), self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.handle_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.handle_rect.centerx = max(self.rect.x, min(event.pos[0], self.rect.right))
                self.value = self.min_val + (self.handle_rect.centerx - self.rect.x) / self.rect.width * (self.max_val - self.min_val)