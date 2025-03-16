# scores_api.py
import requests
import json
import time
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ScoreAPI')


class ScoreAPI:
    def __init__(self, base_url="https://keyscale.lzonca.fr/api", max_retries=3, retry_delay=1):
        self.base_url = base_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logger.info(f"ScoreAPI initialized with base URL: {self.base_url}")

    def _make_api_request(self, method, endpoint, data=None, retries=0):
        """
        Make API request with retry logic
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

            if method.lower() == 'get':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.lower() == 'post':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response

        except requests.exceptions.RequestException as e:
            if retries < self.max_retries:
                logger.warning(
                    f"Request failed ({e}). Retrying in {self.retry_delay}s... ({retries + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
                return self._make_api_request(method, endpoint, data, retries + 1)
            else:
                logger.error(f"API request failed after {self.max_retries} retries: {e}")
                raise

    def get_cli_scores(self):
        """
        Get CLI scores from API
        """
        try:
            response = self._make_api_request('get', 'scores/cli')
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get CLI scores: {e}")
            # Fallback to local JSON
            return self._load_local_json(True)

    def get_game_scores(self):
        """
        Get game scores from API
        """
        try:
            response = self._make_api_request('get', 'scores/game')
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get game scores: {e}")
            # Fallback to local JSON
            return self._load_local_json(False)

    def save_cli_score(self, name, score, letters=0, avg_time=0):
        """
        Save CLI game score to the API
        """
        data = {
            "name": name,
            "score": score,
            "letters": letters,
            "avg_time": avg_time
        }

        try:
            response = self._make_api_request('post', 'scores/cli', data)
            logger.info(f"CLI score saved to API for {name}: {score} points")
            return True
        except Exception as e:
            logger.error(f"Failed to save CLI score to API: {e}")
            # Fallback to local JSON
            self._save_to_local_json(data, is_cli=True)
            return False

    def save_game_score(self, name, score, difficulty="normal"):
        """
        Save graphical game score to the API
        """
        data = {
            "name": name,
            "score": score,
            "difficulty": difficulty
        }

        try:
            response = self._make_api_request('post', 'scores/game', data)
            logger.info(f"Game score saved to API for {name}: {score} points")
            return True
        except Exception as e:
            logger.error(f"Failed to save game score to API: {e}")
            # Fallback to local JSON
            self._save_to_local_json(data, is_cli=False)
            return False

    def _load_local_json(self, is_cli=True):
        """
        Load scores from local JSON file
        """
        file_path = "CLI/scores_CLI.json" if is_cli else "scores.json"

        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load local scores from {file_path}: {e}")
            return []

    def _save_to_local_json(self, score_data, is_cli=True):
        """
        Fallback method to save scores locally if API is unavailable
        """
        file_path = "CLI/scores_CLI.json" if is_cli else "scores.json"

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            # Load existing scores
            scores = []
            try:
                with open(file_path, 'r') as file:
                    scores = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                scores = []

            # Add new score
            scores.append(score_data)

            # Sort by score (descending)
            scores.sort(key=lambda x: x.get('score', 0), reverse=True)

            # Keep only top 10 scores
            scores = scores[:10]

            # Save back to file
            with open(file_path, 'w') as file:
                json.dump(scores, file, indent=4)

            logger.info(f"Score saved locally to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving score locally: {e}")
            return False