
import os
from stortrooper_editor.model import CharacterData, Article

def test_get_available_article_files(res_path):
    """Test finding article files."""
    files = CharacterData.get_available_article_files(res_path, "hero")
    assert "articles.txt" in files

def test_character_data_load(res_path):
    """Test loading character data from file."""
    char_data = CharacterData("hero", res_path)
    char_data.load()
    
    assert len(char_data.articles) == 2
    assert "body" in char_data.categories
    assert "tops" in char_data.categories
    
    body = char_data.get_article_by_id("1")
    assert body.image_name == "body.png"
    assert body.x == 0
    assert body.y == 0
    
    shirt = char_data.get_article_by_id("2")
    assert shirt.image_name == "shirt.png"
    assert shirt.x == 10
    assert shirt.y == 20

def test_layer_z_index(res_path):
    """Test z-index retrieval."""
    char_data = CharacterData("hero", res_path)
    # Don't need to load to check hardcoded z-indices
    
    # Mock an article
    art = Article("x", "img", "cat", "shoes", 0, 0, "-1")
    z = char_data.get_article_z_index(art)
    assert z > 0
    
    art_body = Article("y", "img", "cat", "body", 0, 0, "-1")
    z_body = char_data.get_article_z_index(art_body)
    
    # Shoes should be above body
    assert z > z_body
