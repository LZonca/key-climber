import xml.etree.ElementTree as ET

class Settings:
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = {
            'font_size': 20,
            'square_size': 70,
            'volume': 1.0,
            'display_mode': 'windowed'  # Options: 'fullscreen', 'windowed', 'borderless'
        }
        self.load_settings()

    def load_settings(self):
        try:
            tree = ET.parse(self.settings_file)
            root = tree.getroot()
            self.settings['font_size'] = int(root.find('font_size').text)
            self.settings['square_size'] = int(root.find('square_size').text)
            self.settings['volume'] = float(root.find('volume').text)
            self.settings['display_mode'] = root.find('display_mode').text
        except (ET.ParseError, FileNotFoundError, AttributeError):
            self.save_settings()

    def save_settings(self):
        root = ET.Element('settings')
        ET.SubElement(root, 'font_size').text = str(self.settings['font_size'])
        ET.SubElement(root, 'square_size').text = str(self.settings['square_size'])
        ET.SubElement(root, 'volume').text = str(self.settings['volume'])
        ET.SubElement(root, 'display_mode').text = self.settings['display_mode']
        tree = ET.ElementTree(root)
        tree.write(self.settings_file)