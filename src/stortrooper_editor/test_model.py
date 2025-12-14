import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from stortrooper_editor.model import CharacterData

def test_load():
    res_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../res"))
    char = CharacterData("boy", res_path)
    char.load()
    
    print(f"Categories found: {list(char.categories.keys())}")
    if "body" in char.categories:
        print("First body item:", char.categories["body"][0])

if __name__ == "__main__":
    test_load()
