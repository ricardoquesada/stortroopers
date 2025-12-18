import os
import sys
import unittest

from PySide6.QtWidgets import QApplication

from stortrooper_editor.model import Article, CharacterData
from stortrooper_editor.ui import CanvasWidget, MainWindow

# Adjust path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)


# Mock CharacterData
class MockCharacterData(CharacterData):
    def __init__(self):
        self.name = "MockChar"
        self.articles_filename = "articles.txt"
        self.categories = {
            "body": [Article("1", "body.png", "body", "body", 0, 0, "-1")],
            "hats": [Article("2", "hat.png", "hats", "hats", 0, 0, "-1")],
        }


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = MainWindow("src/res")
        self.window.show()

    def test_state_persistence(self):
        # 1. Setup Canvas and Data
        canvas = CanvasWidget()
        canvas.character_data = MockCharacterData()

        # 2. Initial Refresh (Default Expanded=True)
        self.window.refresh_categories_and_assets(canvas)

        layout = self.window.assets_layout
        box_body = layout.itemAt(0).widget()  # Body Box
        self.assertTrue(
            box_body.toggle_button.isChecked(), "Should default to expanded"
        )

        # 3. User collapses "Body"
        box_body.toggle_button.setChecked(False)
        # Note: setChecked doesn't always emit toggled if via code?
        # QAbstractButton setChecked EMITS toggled if state changes.
        # But let's verify if our lambda captured it.

        self.assertFalse(
            canvas.get_category_expanded("body"), "State should be saved to False"
        )

        # 4. Refresh UI (Simulate tab switch or reload)
        self.window.refresh_categories_and_assets(canvas)

        # 5. Check if state restored
        new_box_body = self.window.assets_layout.itemAt(0).widget()
        self.assertFalse(
            new_box_body.toggle_button.isChecked(), "Should restore collapsed state"
        )
        self.assertFalse(
            new_box_body.content_area.isVisible(), "Content area should be hidden"
        )

        # 6. Check unrelated category "Hats" (should still be True)
        new_box_hats = self.window.assets_layout.itemAt(1).widget()
        self.assertTrue(
            new_box_hats.toggle_button.isChecked(), "Hats should remain expanded"
        )

    def tearDown(self):
        self.window.close()


if __name__ == "__main__":
    unittest.main()
