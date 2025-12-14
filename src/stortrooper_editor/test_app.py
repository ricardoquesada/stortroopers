import sys
import os
import time
from PySide6.QtWidgets import QApplication
from .ui import MainWindow
from .model import CharacterData, Article

def test_app():
    app = QApplication(sys.argv)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_path = os.path.join(base_dir, "res")
    
    print(f"Resource path: {res_path}")
    
    window = MainWindow(res_path)
    
    # 1. Select "boy"
    print("Selecting character 'boy'...")
    index = window.char_combo.findText("boy")
    if index >= 0:
        window.char_combo.setCurrentIndex(index)
        window.load_character()
    else:
        print("Error: 'boy' character not found in combo box")
        return

    # Check if articles loaded
    if not window.current_char_data or len(window.current_char_data.articles) == 0:
        print("Error: No articles loaded for boy")
        return
    else:
        print(f"Loaded {len(window.current_char_data.articles)} articles")

    # 2. Select some items programmatically
    # Find a body
    body_items = window.current_char_data.categories.get("body", [])
    if body_items:
        print(f"Selecting body: {body_items[0].image_name}")
        window.canvas.update_article(body_items[0])
    
    # Find some hair
    hair_items = window.current_char_data.categories.get("hair", [])
    if hair_items:
        print(f"Selecting hair: {hair_items[0].image_name}")
        window.canvas.update_article(hair_items[0])
        
    # Find pants
    pants_items = window.current_char_data.categories.get("bottoms", [])
    if pants_items:
        print(f"Selecting bottoms: {pants_items[0].image_name}")
        window.canvas.update_article(pants_items[0])

    # 3. Save Image
    output_path = os.path.join(base_dir, "test_output.png")
    print(f"Saving to {output_path}...")
    window.canvas.save_image(output_path)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"Success: Image created, size {size} bytes")
    else:
        print("Error: Image not created")

if __name__ == "__main__":
    # Add current dir to path so we can import ui and model
    sys.path.append(os.path.dirname(__file__))
    test_app()
