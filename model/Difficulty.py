# model/Difficulty.py
class Difficulty:
    def __init__(self, name, obstacle_speed, spawn_rate, lava_speed_increment):
        self.name = name
        self.obstacle_speed = obstacle_speed
        self.spawn_rate = spawn_rate
        self.lava_speed_increment = lava_speed_increment