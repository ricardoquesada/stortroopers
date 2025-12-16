
import os
import pytest

@pytest.fixture
def res_path(tmp_path):
    """Creates a temporary resource directory structure for testing."""
    res = tmp_path / "res"
    res.mkdir()
    
    # Create a character directory
    char_dir = res / "hero"
    char_dir.mkdir()
    
    # Create articles.txt
    articles_content = """
# This is a comment
"HCDataSetFile_data" "1.0"

"1" "body.png" "body" "body" "0" "0" "-1"
"2" "shirt.png" "tops" "tops" "10" "20" "-1"
    """
    (char_dir / "articles.txt").write_text(articles_content, encoding="utf-8")
    
    # Create data directory and dummy images
    data_dir = char_dir / "data"
    data_dir.mkdir()
    (data_dir / "body.png").touch()
    (data_dir / "shirt.png").touch()
    
    return str(res)
