
import pytest
from PySide6.QtWidgets import QApplication
from stortrooper_editor.ui import CanvasWidget
from stortrooper_editor.model import Article, CharacterData
import os

# Need a qapp for GUI widgets, pytest-qt provides this automatically usually, 
# but if we run headless or without display, we might need care.
# For simple logic tests, we might get away with it.

def test_canvas_lifecycle(qtbot):
    """Test creation of CanvasWidget."""
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    assert canvas.scene is not None

def test_canvas_update_article(qtbot, mocker):
    """Test adding an article to the canvas."""
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    
    # Mock CharacterData
    char_data = mocker.Mock(spec=CharacterData)
    char_data.get_article_z_index.return_value = 10
    canvas.set_character(char_data)
    
    # Create a dummy article
    # We need a real image path or QPixmap will fail/be null.
    # We can mock QPixmap or provide a dummy image. 
    # Let's mock QPixmap in ui.py or just let it fail gracefully?
    # The code says: if pixmap.isNull(): return
    
    article = Article("1", "test.png", "body", "body", 0, 0, "-1", local_path="non_existent.png")
    
    # It should log error and return if image not found
    canvas.update_article(article)
    assert "body" not in canvas.active_articles
    
    # Now let's try with a valid pixmap or mock
    # Mocking QPixmap is hard because it's C++. 
    # Better to create a fake image file.
    
    import tempfile
    from PySide6.QtGui import QImage, QColor
    
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img = QImage(10, 10, QImage.Format_ARGB32)
        img.fill(QColor("red"))
        img.save(tmp.name)
        article.local_path = tmp.name
        
        canvas.update_article(article)
        
        assert "body" in canvas.active_articles
        assert "body" in canvas.pixmap_items
        
    os.remove(tmp.name)

def test_canvas_remove_article(qtbot, mocker):
    """Test removing an article."""
    canvas = CanvasWidget()
    qtbot.addWidget(canvas)
    
    char_data = mocker.Mock(spec=CharacterData)
    char_data.get_article_z_index.return_value = 10
    canvas.set_character(char_data)
    
    # Create valid article logic again... 
    # Ideally refactor helper, but explicit here is fine.
    import tempfile
    from PySide6.QtGui import QImage, QColor
    
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img = QImage(10, 10, QImage.Format_ARGB32)
        img.fill(QColor("red"))
        img.save(tmp.name)
        
        article = Article("1", "test.png", "body", "body", 0, 0, "-1", local_path=tmp.name)
        canvas.update_article(article)
        
        assert canvas.is_article_active(article)
        
        canvas.remove_article(article)
        assert not canvas.is_article_active(article)
        
    os.remove(tmp.name)
