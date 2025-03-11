class Player:
    def __init__(self):
        self.lives = 4
        self.name = None

    def lose_life(self):
        """Decreases player's life count by 1."""
        self.lives -= 1