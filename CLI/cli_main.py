import argparse
import random
import sys
import time
import keyboard
import json
import os
import traceback

from CLI.model.player import Player
from scores_api import ScoreAPI

scores_file = "scores_CLI.json"

class Game:
    def __init__(self):
        self.player = Player()
        self.score = 0
        self.correct_letters = 0
        self.running = True
        self.available_keys = ["A", "S", "D", "W", "Z", "Q", "E", "R", "T", "Y", "U", "I", "O", "P", "F", "G", "H", "J",
                              "K", "L", "X", "C", "V", "B", "N", "M"]
        self.high_scores = self.get_high_scores()
        self.reaction_times = []

        # Get player name during initialization before the game starts
        self.initialize_player()

    def initialize_player(self):
        """Initialize the player with name input"""
        print("Bienvenue dans la console!")
        self.player.name = self.get_player_name()
        print(f"Bon jeu, {self.player.name}!")

    def generate_key(self):
        return random.choice(self.available_keys)

    def reset_game(self):
        self.player = Player()
        self.score = 0
        self.correct_letters = 0
        self.reaction_times = []
        self.running = True
        self.initialize_player()  # Re-ask for player name on reset

    # Add this method to your Game class
    def get_high_scores(self):
        """Retrieve high scores from API with fallback to local file"""
        try:
            # Try API first
            api = ScoreAPI()
            try:
                scores = api.get_cli_scores()
                if scores:
                    return scores
            except Exception as e:
                print(f"Error retrieving scores from API: {e}")
                print("Falling back to local scores")

            # Fallback to local file
            if os.path.exists("CLI/scores_CLI.json"):
                with open("CLI/scores_CLI.json", 'r') as f:
                    return json.load(f)
            else:
                # Create the file with an empty array if it doesn't exist
                os.makedirs(os.path.dirname("CLI/scores_CLI.json"), exist_ok=True)
                with open("CLI/scores_CLI.json", 'w') as f:
                    json.dump([], f)
                return []
        except Exception as e:
            print(f"Error handling high scores: {e}")
            return []

    def view_high_scores(self):
        score_api = ScoreAPI()

        try:
            # Try API first
            try:
                scores = score_api.get_cli_scores()
                print("Scores retrieved from API")
            except Exception as e:
                print(f"Could not retrieve scores from API: {e}")
                print("Falling back to local scores")

                # Fallback to local file
                with open(scores_file, 'r') as file:
                    scores = json.load(file)

            if not scores:
                print("Aucun score enregistré pour le moment.")
                return

            print("\n╔═════════════════════════════════════════════════════════════════════╗")
            print("║                           MEILLEURS SCORES                          ║")
            print("╠═══════╦═══════════════════╦════════╦════════════╦═══════════════════╣")
            print("║ Rang  ║ Joueur            ║ Score  ║ Lettres    ║ Temps moyen (s)   ║")
            print("╠═══════╬═══════════════════╬════════╬════════════╬═══════════════════╣")

            for i, score_data in enumerate(scores):
                name = score_data.get("name", "Anonyme")
                score = score_data.get("score", 0)
                letters = score_data.get("letters", 0)
                avg_time = score_data.get("avg_time", 0)
                print(f"║ {i + 1:<5} ║ {name[:17]:<17} ║ {score:<6} ║ {letters:<10} ║ {avg_time:<17} ║")

            print("╚═══════╩═══════════════════╩════════╩════════════╩═══════════════════╝\n")
        except FileNotFoundError:
            print("Aucun score enregistré. Soyez le premier à établir un record!")
        except json.JSONDecodeError:
            print("Erreur de lecture du fichier de scores. Le fichier est peut-être corrompu.")

    def get_player_name(self):
        print("\n╔═══════════════════════════════════╗")
        print("║        NOUVELLE PARTIE            ║")
        print("╚═══════════════════════════════════╝\n")

        player_name = input("Entrez votre nom (max 17 caractères): ").strip()[:17]

        if not player_name:
            player_name = "Anonyme"

        return player_name

    def update_high_scores(self, player_name, score):
        """Update high scores in API and local file"""
        try:
            # Calculate average reaction time
            avg_time = 0
            if self.reaction_times:
                avg_time = sum(self.reaction_times) / len(self.reaction_times)
                avg_time = round(avg_time, 2)

            # First try to save to API
            api = ScoreAPI()
            api_success = api.save_cli_score(
                name=player_name,
                score=score,
                letters=self.correct_letters,
                avg_time=avg_time
            )

            # Now update local file regardless of API success
            if not os.path.exists("CLI/scores_CLI.json"):
                os.makedirs(os.path.dirname("CLI/scores_CLI.json"), exist_ok=True)
                with open("CLI/scores_CLI.json", 'w') as f:
                    json.dump([], f)

            try:
                with open("CLI/scores_CLI.json", 'r') as f:
                    high_scores = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                high_scores = []

            # Add new score
            new_score = {
                "name": player_name,
                "score": score,
                "letters": self.correct_letters,
                "avg_time": avg_time
            }
            high_scores.append(new_score)

            # Sort by score (descending)
            high_scores.sort(key=lambda x: x.get("score", 0), reverse=True)

            # Keep only top 10 scores
            high_scores = high_scores[:10]

            # Save back to file
            with open("CLI/scores_CLI.json", 'w') as f:
                json.dump(high_scores, f, indent=4)

            self.high_scores = high_scores
            return True
        except Exception as e:
            print(f"Error updating high scores: {e}")
            traceback.print_exc()
            return False

    def run(self):
        try:
            max_reaction_time = 5

            while self.running:
                try:
                    if self.player.lives <= 0:
                        print("\n╔═══════════════════════════════════╗")
                        print(f"║  PARTIE TERMINÉE! Score: {self.score:<8} ║")
                        print("╚═══════════════════════════════════╝\n")

                        # Use the name collected at the start
                        self.update_high_scores(self.player.name, self.score)

                        lowest_high_score = 0
                        if self.high_scores and len(self.high_scores) >= 10:
                            lowest_high_score = self.high_scores[-1]["score"]

                        if not self.high_scores or self.score > lowest_high_score or len(self.high_scores) < 10:
                            print("\n🎉 Félicitations! Vous êtes dans le tableau des meilleurs scores! 🎉")

                        restart_choice = input("\nAppuyez sur R pour recommencer ou une autre touche pour quitter: ").strip().upper()

                        if restart_choice == 'R':
                            self.reset_game()  # reset_game now calls initialize_player
                        else:
                            self.running = False

                        continue

                    # Game loop logic
                    random_delay = random.uniform(0, 5)
                    print("À vos marques...")
                    time.sleep(random_delay / 3)
                    print("Prêt...")
                    time.sleep(random_delay / 3)
                    print("ECRIVEZ!")

                    target_key = self.generate_key()
                    print(f"Appuyez sur la touche: {target_key} (Vous avez {max_reaction_time:.1f}s)")

                    start_time = time.time()
                    key_pressed = False

                    # Maintain the keyboard-based detection that was working before
                    while not key_pressed and time.time() - start_time < max_reaction_time:
                        if keyboard.is_pressed(target_key):
                            # Correct key
                            end_time = time.time()
                            reaction_time = end_time - start_time
                            self.correct_letters += 1
                            self.reaction_times.append(reaction_time)
                            time_percentage = reaction_time / max_reaction_time
                            points = int(500 * (1 - time_percentage))
                            points = max(10, points)
                            self.score += points
                            print(f"Correct! Temps de réaction: {reaction_time:.2f}s - Vous gagnez {points} points! Score total: {self.score}")
                            time.sleep(0.5)
                            key_pressed = True
                        else:
                            for key in self.available_keys:
                                if key != target_key and keyboard.is_pressed(key):
                                    self.player.lose_life()
                                    print(f"Mauvaise touche! Vies restantes: {self.player.lives}")
                                    time.sleep(0.5)
                                    key_pressed = True
                                    break
                        time.sleep(0.01)

                    # Handle timeout
                    if not key_pressed:
                        self.player.lose_life()
                        print(f"Trop lent! Temps écoulé. Vies restantes: {self.player.lives}")
                        time.sleep(0.5)

                    # Adjust difficulty based on average reaction time
                    if len(self.reaction_times) >= 3:
                        recent_times = self.reaction_times[-5:] if len(self.reaction_times) >= 5 else self.reaction_times
                        avg_reaction_time = sum(recent_times) / len(recent_times)

                        print(f"Temps de réaction moyen: {avg_reaction_time:.2f}s")

                        # Adjust max time based on average reaction time
                        old_time = max_reaction_time
                        new_time = min(5, max(1.25, avg_reaction_time * 1.5))

                        if abs(new_time - old_time) >= 0.2:
                            max_reaction_time = round(new_time, 1)
                            if new_time < old_time:
                                print(f"Difficulté augmentée! Vous avez maintenant {max_reaction_time:.1f}s pour réagir.")
                            else:
                                print(f"Difficulté ajustée à {max_reaction_time:.1f}s basé sur votre temps de réaction moyen.")

                except KeyboardInterrupt:
                    print("\n\nJeu interrompu. Voulez-vous quitter? (O/N)")
                    try:
                        response = input().strip().upper()
                        if response == "O":
                            self.running = False
                            break
                    except:
                        self.running = False
                        break

        except KeyboardInterrupt:
            print("\n\nJeu terminé par l'utilisateur.")


def view_high_scores():
    score_api = ScoreAPI()

    try:
        # Try API first
        try:
            scores = score_api.get_cli_scores()
            print("Scores retrieved from API")
        except Exception as e:
            print(f"Could not retrieve scores from API: {e}")
            print("Falling back to local scores")

            # Fallback to local file
            with open("CLI/scores_CLI.json", 'r') as file:  # Updated path
                scores = json.load(file)

        if not scores:
            print("Aucun score enregistré pour le moment.")
            return

        print("\n╔═════════════════════════════════════════════════════════════════════╗")
        print("║                           MEILLEURS SCORES                          ║")
        print("╠═══════╦═══════════════════╦════════╦════════════╦═══════════════════╣")
        print("║ Rang  ║ Joueur            ║ Score  ║ Lettres    ║ Temps moyen (s)   ║")
        print("╠═══════╬═══════════════════╬════════╬════════════╬═══════════════════╣")

        for i, score_data in enumerate(scores):
            name = score_data.get("name", "Anonyme")
            score = score_data.get("score", 0)
            letters = score_data.get("letters", 0)
            avg_time = score_data.get("avg_time", 0)
            print(f"║ {i + 1:<5} ║ {name[:17]:<17} ║ {score:<6} ║ {letters:<10} ║ {avg_time:<17} ║")

        print("╚═══════╩═══════════════════╩════════╩════════════╩═══════════════════╝\n")
    except FileNotFoundError:
        print("Aucun score enregistré. Soyez le premier à établir un record!")
    except json.JSONDecodeError:
        print("Erreur de lecture du fichier de scores. Le fichier est peut-être corrompu.")

def main():
    parser = argparse.ArgumentParser(description="Jeu de réflexes CLI")
    parser.add_argument('command', choices=['start', 'highscores', 'sync'], help="Commande à exécuter", nargs='?', default='start')
    args = parser.parse_args()

    if args.command == 'start':
        game = Game()
        game.run()
        print("Merci d'avoir joué!")
        input("Appuyez sur Entrée pour quitter...")
    elif args.command == 'highscores':
        view_high_scores()
    elif args.command == 'sync':
        print("Synchronisation des scores locaux avec le serveur...")
        score_api = ScoreAPI()
        try:
            score_api.sync_local_scores()
            print("Synchronisation terminée!")
        except Exception as e:
            print(f"Erreur lors de la synchronisation: {e}")

if __name__ == "__main__":
    main()