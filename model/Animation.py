import pygame
import numpy as np
from PIL import Image
import threading
import time


class Animation:
    def __init__(self, filepath, screen_width, screen_height, skip_fade_in=False):
        self.frames = []
        self.current_frame = 0
        self.frame_count = 0
        self.frame_delay = 5  # Controls animation speed
        self.delay_counter = 0
        self.done = False
        self.alpha = 255 if skip_fade_in else 0  # Full opacity if skip_fade_in is True
        self.fade_speed = 5
        self.fade_in = not skip_fade_in  # Skip fade-in if requested
        self.complete_loops = 0
        self.max_loops = 1  # Play only once
        self.fade_out_started = False
        self.min_display_frames = 10
        self.displayed_frames = 0
        self.loading_complete = False
        self.loading_thread = None
        self.loading_error = None
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.filepath = filepath
        self.skip_fade_in = skip_fade_in

        # Start loading thread
        self.loading_thread = threading.Thread(target=self._load_gif_thread)
        self.loading_thread.start()
        print(f"Started loading animation from {filepath} in background thread")

    def _load_gif_thread(self):
        """Thread function to load GIF animation frames"""
        try:
            # Set thread priority higher
            import os
            try:
                os.nice(-10)  # Lower nice value = higher priority (Unix-like systems)
            except (OSError, AttributeError):
                pass  # Ignore if not supported on Windows

            # Open the GIF file with PIL
            gif = Image.open(self.filepath)
            temp_frames = []
            frame_count = 0

            # Iterate through all frames
            try:
                while True:
                    # Convert to RGBA
                    frame = gif.convert("RGBA")

                    # Convert PIL image to Pygame surface
                    frame_data = frame.tobytes()
                    frame_size = frame.size
                    pygame_frame = pygame.image.fromstring(frame_data, frame_size, "RGBA")

                    # Scale the image to fit the screen
                    scaled_frame = pygame.transform.scale(pygame_frame, (self.screen_width, self.screen_height))
                    temp_frames.append(scaled_frame)

                    # Move to next frame
                    frame_count += 1
                    gif.seek(gif.tell() + 1)

            except EOFError:
                # End of sequence
                pass

            self.frame_count = frame_count
            self.frames = temp_frames  # Atomically assign all frames at once

            # Set appropriate frame delay - use a minimum of 2 to ensure animation is visible
            if hasattr(gif, 'info') and 'duration' in gif.info:
                # Convert from ms to frames but ensure it's not too quick
                self.frame_delay = max(2, int(gif.info['duration'] / 33))
                print(f"Setting frame delay to {self.frame_delay} based on GIF duration")
            else:
                # Default to a reasonable speed if no duration info
                self.frame_delay = 2

            # Ensure minimum display time is adequate
            self.min_display_frames = max(60, self.frame_count * 2)

            print(f"Loaded {self.frame_count} frames from {self.filepath}")
            self.loading_complete = True

        except Exception as e:
            self.loading_error = str(e)
            print(f"Error loading GIF: {e}")
            self.loading_complete = True  # Mark as complete even on error
            self.done = True  # Mark animation as done to avoid displaying incomplete content

    def update(self):
        # If still loading, don't update animation state
        if not self.loading_complete or len(self.frames) == 0:
            return

        # First handle fade-in
        if self.fade_in and self.alpha < 255:
            self.alpha += self.fade_speed
            if self.alpha >= 255:
                self.alpha = 255
                self.fade_in = False
            return

        # Count frames displayed at full opacity
        if not self.fade_in and not self.fade_out_started:
            self.displayed_frames += 1

        # Process animation frames
        self.delay_counter += 1
        if self.delay_counter >= self.frame_delay:
            self.delay_counter = 0
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                if self.complete_loops >= self.max_loops - 1:
                    self.current_frame = len(self.frames) - 1

                    # Only start fade-out if minimum display time has passed
                    if self.displayed_frames >= self.min_display_frames:
                        self.fade_out_started = True
                else:
                    self.current_frame = 0
                    self.complete_loops += 1

        # Handle fade-out only after minimum display time
        if self.fade_out_started:
            self.alpha -= self.fade_speed
            if self.alpha <= 0:
                self.alpha = 0
                self.done = True

    def draw(self, screen):
        # If still loading or no frames, show loading indicator
        if not self.loading_complete or len(self.frames) == 0:
            if self.loading_error:
                error_font = pygame.font.Font(None, 24)
                error_text = error_font.render(f"Error: {self.loading_error}", True, (255, 0, 0))
                screen.blit(error_text, (10, 40))
            else:
                loading_font = pygame.font.Font(None, 36)
                loading_text = loading_font.render("Loading animation...", True, (255, 255, 255))
                screen.blit(loading_text, (self.screen_width // 2 - loading_text.get_width() // 2,
                                           self.screen_height // 2 - loading_text.get_height() // 2))
            return

        if self.current_frame >= len(self.frames):
            return

        frame_copy = self.frames[self.current_frame].copy()
        frame_copy.set_alpha(self.alpha)

        screen.blit(frame_copy, (0, 0))

        debug_font = pygame.font.Font(None, 24)
        debug_info = f"Frame: {self.current_frame + 1}/{self.frame_count} | Alpha: {self.alpha} | Loops: {self.complete_loops}/{self.max_loops}"
        debug_text = debug_font.render(debug_info, True, (255, 255, 255))
        screen.blit(debug_text, (10, 10))

    def load_gif(self, filepath, screen_width, screen_height):
        """Load and process GIF animation frames"""
        try:
            # Open the GIF file with PIL
            gif = Image.open(filepath)

            # Reset frame lists
            self.frames = []

            # Process all frames
            frame_count = 0

            # Iterate through all frames
            try:
                while True:
                    # Convert to RGBA
                    frame = gif.convert("RGBA")

                    # Convert PIL image to Pygame surface
                    frame_data = frame.tobytes()
                    frame_size = frame.size
                    pygame_frame = pygame.image.fromstring(frame_data, frame_size, "RGBA")

                    # Scale the image to fit the screen
                    scaled_frame = pygame.transform.scale(pygame_frame, (screen_width, screen_height))
                    self.frames.append(scaled_frame)

                    # Move to next frame
                    frame_count += 1
                    gif.seek(gif.tell() + 1)

            except EOFError:
                # End of sequence
                pass

            self.frame_count = frame_count
            print(f"Loaded {self.frame_count} frames from {filepath}")

            # Set appropriate frame delay - use a minimum of 3 to ensure animation is visible
            if hasattr(gif, 'info') and 'duration' in gif.info:
                # Convert from ms to frames but ensure it's not too quick
                self.frame_delay = max(3, int(gif.info['duration'] / 33))
                print(f"Setting frame delay to {self.frame_delay} based on GIF duration")
            else:
                # Default to a reasonable speed if no duration info
                self.frame_delay = 3

            # Increase the number of loops to ensure animation is visible
            self.max_loops = 2

            # Ensure minimum display time is adequate
            self.min_display_frames = max(60, self.frame_count * 2)

            return True
        except Exception as e:
            print(f"Error loading GIF: {e}")
            return False