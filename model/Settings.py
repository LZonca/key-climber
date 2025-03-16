# model/Settings.py
import xml.etree.ElementTree as ET


class Settings:
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        try:
            tree = ET.parse(self.settings_file)
            root = tree.getroot()

            # Get general volume (for backward compatibility)
            volume_element = root.find('volume')
            general_volume = float(volume_element.text) if volume_element is not None else 0.5

            # Get specific volume settings or use general volume as default
            self.settings['menu_music_volume'] = float(
                root.find('menu_music_volume').text if root.find('menu_music_volume') is not None else general_volume)
            self.settings['game_music_volume'] = float(
                root.find('game_music_volume').text if root.find('game_music_volume') is not None else general_volume)
            self.settings['sound_effects_volume'] = float(root.find('sound_effects_volume').text if root.find(
                'sound_effects_volume') is not None else general_volume)

            # Legacy volume setting (can be removed later)
            self.settings['volume'] = general_volume

            self.settings['font_size'] = int(float(root.find('font_size').text))
            self.settings['square_size'] = int(float(root.find('square_size').text))
            self.settings['display_mode'] = root.find('display_mode').text
            self.settings['difficulty'] = root.find('difficulty').text
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Set default values if settings file couldn't be loaded
            self.settings['menu_music_volume'] = 0.5
            self.settings['game_music_volume'] = 0.5
            self.settings['sound_effects_volume'] = 0.5
            self.settings['volume'] = 0.5
            self.settings['font_size'] = 36
            self.settings['square_size'] = 30
            self.settings['display_mode'] = 'window'
            self.settings['difficulty'] = 'moyen'

    def save_settings(self):
        tree = ET.ElementTree(ET.Element('settings'))
        root = tree.getroot()

        # Save all volume settings
        ET.SubElement(root, 'menu_music_volume').text = str(self.settings['menu_music_volume'])
        ET.SubElement(root, 'game_music_volume').text = str(self.settings['game_music_volume'])
        ET.SubElement(root, 'sound_effects_volume').text = str(self.settings['sound_effects_volume'])

        # Legacy volume (for compatibility)
        ET.SubElement(root, 'volume').text = str(self.settings['volume'])

        ET.SubElement(root, 'font_size').text = str(self.settings['font_size'])
        ET.SubElement(root, 'square_size').text = str(self.settings['square_size'])
        ET.SubElement(root, 'display_mode').text = self.settings['display_mode']
        ET.SubElement(root, 'difficulty').text = self.settings['difficulty']
        tree.write(self.settings_file)