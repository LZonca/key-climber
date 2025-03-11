import pygame


class DifficultySelector:
    def __init__(self, x, y, width, height, difficulties, current_difficulty):
        self.rect = pygame.Rect(x, y, width, height)
        self.difficulties = difficulties
        self.current_index = difficulties.index(current_difficulty)
        self.font = pygame.font.Font(None, 36)
        self.left_arrow_rect = pygame.Rect(x - 30, y, 30, height)
        self.right_arrow_rect = pygame.Rect(x + width, y, 30, height)

    def draw(self, screen):
        pygame.draw.rect(screen, (200, 200, 200), self.rect)

        # Function to draw text with border
        def draw_text_with_border(text, x, y):
            border_color = (255, 255, 255)  # White border color
            screen.blit(self.font.render(text, True, border_color), (x - 2, y - 2))
            screen.blit(self.font.render(text, True, border_color), (x + 2, y - 2))
            screen.blit(self.font.render(text, True, border_color), (x - 2, y + 2))
            screen.blit(self.font.render(text, True, border_color), (x + 2, y + 2))
            screen.blit(self.font.render(text, True, (0, 0, 0)), (x, y))  # Main text

        difficulty_text = self.difficulties[self.current_index]
        draw_text_with_border(difficulty_text, self.rect.x + 10, self.rect.y + 10)

        left_arrow = "<"
        right_arrow = ">"
        draw_text_with_border(left_arrow, self.left_arrow_rect.x, self.left_arrow_rect.y + 10)
        draw_text_with_border(right_arrow, self.right_arrow_rect.x, self.right_arrow_rect.y + 10)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = event.pos
                if self.left_arrow_rect.collidepoint(mouse_pos):
                    self.current_index = (self.current_index - 1) % len(self.difficulties)
                elif self.right_arrow_rect.collidepoint(mouse_pos):
                    self.current_index = (self.current_index + 1) % len(self.difficulties)

    def get_current_difficulty(self):
        return self.difficulties[self.current_index]