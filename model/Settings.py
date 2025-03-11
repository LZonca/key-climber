# model/Settings.py
import xml.etree.ElementTree as ET

class Settings:
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        tree = ET.parse(self.settings_file)
        root = tree.getroot()
        self.settings['volume'] = float(root.find('volume').text)
        self.settings['font_size'] = int(float(root.find('font_size').text))
        self.settings['square_size'] = int(float(root.find('square_size').text))
        self.settings['display_mode'] = root.find('display_mode').text
        self.settings['difficulty'] = root.find('difficulty').text

    def save_settings(self):
        tree = ET.ElementTree(ET.Element('settings'))
        root = tree.getroot()
        ET.SubElement(root, 'volume').text = str(self.settings['volume'])
        ET.SubElement(root, 'font_size').text = str(self.settings['font_size'])
        ET.SubElement(root, 'square_size').text = str(self.settings['square_size'])
        ET.SubElement(root, 'display_mode').text = self.settings['display_mode']
        ET.SubElement(root, 'difficulty').text = self.settings['difficulty']
        tree.write(self.settings_file)