import pygame

class Lava:
    def __init__(self, width, height, speed, image_path):
        # Position the lava at the bottom of the screen, visible
        screen_height = pygame.display.Info().current_h
        self.rect = pygame.Rect(0, screen_height - 50, width, 50)
        self.speed = speed
        self.moving_up = True
        self.target_position = self.rect.y
        self.image = pygame.image.load(image_path)
        self.original_image = self.image
        self.start_delay = 0  # Default to 0 seconds
        self.start_time = pygame.time.get_ticks()
        self.moving_enabled = False

    def set_start_delay(self, delay_seconds):
        self.start_delay = delay_seconds
        self.start_time = pygame.time.get_ticks()
        self.moving_enabled = False

    def update_position(self):
        # Check if the delay period has passed
        if not self.moving_enabled:
            if pygame.time.get_ticks() - self.start_time >= self.start_delay * 1000:
                self.moving_enabled = True
                return  # Don't move on the first frame when enabled

        # Only move if movement is enabled
        if self.moving_enabled:
            if self.moving_up:
                # Moving up logic
                self.rect.y -= self.speed
                # Check if lava has reached too high, then start moving down
                if self.rect.y <= 0:  # Prevent going above screen
                    self.rect.y = 0
                    self.moving_up = False
                    self.target_position = pygame.display.Info().current_h - 50
            else:
                # Moving down logic
                if self.rect.y < self.target_position:
                    self.rect.y += self.speed * 2  # Move down faster
                    # Debug print
                    print(f"Moving down: {self.rect.y}/{self.target_position}")
                else:
                    # We've reached or passed the target position, switch direction
                    print("Reached target position, switching to moving up")
                    self.rect.y = min(self.rect.y, self.target_position)  # Make sure we don't go too far
                    self.moving_up = True  # Start moving up again

    def speed_up(self, amount=None):
        """Increase the lava speed when a key falls into it with a maximum cap"""
        # Define maximum lava speed
        max_speed = 10

        # Use the provided amount or default to 0.2
        increment = amount if amount is not None else 0.2

        # Calculate new speed
        new_speed = self.speed + increment

        # Apply the cap
        if new_speed <= max_speed:
            self.speed = new_speed
            print(f"Lava speed increased to {self.speed}")
        else:
            self.speed = max_speed
            print(f"Lava reached maximum speed of {self.speed}")

    def move_down(self, amount):
        current_y = self.rect.y
        self.target_position = min(current_y + amount, pygame.display.Info().current_h - 50)
        self.moving_up = False
        self.moving_enabled = True  # Ensure movement is enabled

        # Debug print to verify movement
        print(f"Moving lava down: current={current_y}, target={self.target_position}")

    def increase_speed(self, increment):
        self.speed += increment

    def reset_position(self):
        self.rect.y = pygame.display.Info().current_h - 50
        self.target_position = self.rect.y

    def draw(self, screen):
        height = pygame.display.Info().current_h - self.rect.y
        scaled_image = pygame.transform.scale(self.original_image, (self.rect.width, height))
        screen.blit(scaled_image, (self.rect.x, self.rect.y))