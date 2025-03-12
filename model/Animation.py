import imageio
import pygame
from PIL import Image
import numpy as np

class Animation:
    def __init__(self, filepath, screen_width, screen_height):
        self.frames = []
        self.current_frame = 0
        self.frame_count = 0
        self.alpha = 0  # For fade in
        self.done = False

        # Load and prepare the GIF
        self.load_gif(filepath, screen_width, screen_height)

    def load_gif(self, filepath, screen_width, screen_height):
        try:
            gif = imageio.get_reader(filepath)
            for frame in gif:
                # Convert to pygame surface
                frame_rgb = np.array(frame)
                surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))

                # Scale to fit screen
                scaled_surface = pygame.transform.scale(surface, (screen_width, screen_height))
                self.frames.append(scaled_surface)

            self.frame_count = len(self.frames)
        except Exception as e:
            print(f"Error loading animation: {e}")
            self.frames = [pygame.Surface((screen_width, screen_height))]
            self.frame_count = 1

    def update(self):
        # Fade in logic
        if self.alpha < 255:
            self.alpha += 5  # Speed of fade in

        # Advance frame counter
        if pygame.time.get_ticks() % 5 == 0:  # Control animation speed
            self.current_frame = (self.current_frame + 1) % self.frame_count
            if self.current_frame == 0 and self.alpha >= 255:
                self.done = True

    def draw(self, screen):
        if not self.frames:
            return

        # Create a copy of the current frame to modify alpha
        frame_copy = self.frames[self.current_frame].copy()

        # Apply alpha for fade in
        frame_copy.set_alpha(self.alpha)

        # Draw the frame
        screen.blit(frame_copy, (0, 0))