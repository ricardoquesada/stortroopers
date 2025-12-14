import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QComboBox, QListWidget, QListWidgetItem, QLabel, 
    QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QFileDialog, QTabWidget, QMessageBox, QScrollArea
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QIcon
from PySide6.QtCore import Qt, QSize, QRectF
from .model import CharacterData, Article

class CanvasWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing, False) # Pixel art, keep it sharp?
        self.setRenderHint(QPainter.SmoothPixmapTransform, False)
        # Fixed size for scene, maybe? Or dynamic?
        # The coordinates in articles.txt seem to operate in a specific space.
        # Let's assume a reasonable canvas size, maybe 400x400 or just enough to fit.
        # Based on coords like y=128 for shoes, it's not huge.
        self.scene.setSceneRect(0, 0, 300, 300)
        self.active_articles = {} # layer_name -> Article
        self.pixmap_items = {} # layer_name -> QGraphicsPixmapItem

    def set_character(self, character_data: CharacterData):
        self.character_data = character_data
        self.clear()
        
    def clear(self):
        self.active_articles = {}
        self.scene.clear()
        self.pixmap_items = {}

    def update_article(self, article: Article):
        # Remove existing item on this layer if any
        if article.layer_name in self.pixmap_items:
            # Check if it's the same article, if so, maybe toggle off?
            # For now, just replace.
            self.scene.removeItem(self.pixmap_items[article.layer_name])
            del self.pixmap_items[article.layer_name]
        
        # Load image
        pixmap = QPixmap(article.local_path)
        if pixmap.isNull():
            print(f"Failed to load image: {article.local_path}")
            return

        item = QGraphicsPixmapItem(pixmap)
        item.setPos(article.x, article.y)
        
        # Z-Index
        z = self.character_data.get_article_z_index(article)
        item.setZValue(z)
        
        self.scene.addItem(item)
        self.pixmap_items[article.layer_name] = item
        self.active_articles[article.layer_name] = article

    def save_image(self, file_path):
        # Create an image with the scene's dimensions
        rect = self.scene.itemsBoundingRect()
        if rect.isEmpty():
            rect = QRectF(0, 0, 300, 300)
            
        # Add some padding
        rect.adjust(-10, -10, 10, 10)
        
        image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        painter = QPainter(image)
        self.scene.render(painter, target=QRectF(image.rect()), source=rect)
        painter.end()
        
        image.save(file_path)

class AssetSelector(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(64, 64))
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(10)

class MainWindow(QMainWindow):
    def __init__(self, res_path):
        super().__init__()
        self.setWindowTitle("StorTrooper Character Editor")
        self.resize(1000, 700)
        self.res_path = res_path
        self.current_char_data = None
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left Panel: Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel, 1)
        
        # Character Selector
        self.char_combo = QComboBox()
        self.char_combo.currentIndexChanged.connect(self.load_character)
        left_layout.addWidget(QLabel("Character Type:"))
        left_layout.addWidget(self.char_combo)
        
        # Category Tabs
        self.category_tabs = QTabWidget()
        self.category_tabs.currentChanged.connect(self.on_category_changed)
        left_layout.addWidget(self.category_tabs)
        
        # Asset List
        self.asset_list = AssetSelector()
        self.asset_list.itemClicked.connect(self.on_asset_clicked)
        left_layout.addWidget(self.asset_list)
        
        # Save Button
        save_btn = QPushButton("Save Character to PNG")
        save_btn.clicked.connect(self.save_character)
        left_layout.addWidget(save_btn)

        # Right Panel: Canvas
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, 2)
        
        self.canvas = CanvasWidget()
        right_layout.addWidget(self.canvas)
        
        # Populate Characters
        self.populate_characters()

    def populate_characters(self):
        # Scan res_path for directories
        if not os.path.exists(self.res_path):
            QMessageBox.critical(self, "Error", f"Resource path not found: {self.res_path}")
            return

        chars = [d for d in os.listdir(self.res_path) 
                 if os.path.isdir(os.path.join(self.res_path, d)) and d != "data" and not d.startswith(".")]
        chars.sort()
        self.char_combo.addItems(chars)

    def load_character(self):
        char_name = self.char_combo.currentText()
        if not char_name:
            return
            
        self.current_char_data = CharacterData(char_name, self.res_path)
        self.current_char_data.load()
        
        self.canvas.set_character(self.current_char_data)
        
        # Update Categories
        self.category_tabs.clear()
        
        # Define a consistent order if possible, or alphabetical
        categories = sorted(list(self.current_char_data.categories.keys()))
        
        # Prioritize body/skin
        if "body" in categories:
            categories.insert(0, categories.pop(categories.index("body")))
            
        for cat in categories:
            self.category_tabs.addTab(QWidget(), cat)
            
        if self.category_tabs.count() > 0:
            self.on_category_changed(0)
            
        # Try to set default body if available
        if "body" in self.current_char_data.categories:
             # Just pick the first body
             first_body = self.current_char_data.categories["body"][0]
             self.canvas.update_article(first_body)

    def on_category_changed(self, index):
        if index < 0:
            return
        cat_name = self.category_tabs.tabText(index)
        
        self.asset_list.clear()
        
        if not self.current_char_data:
            return
            
        articles = self.current_char_data.categories.get(cat_name, [])
        for article in articles:
            item = QListWidgetItem(article.image_name) # Use simpler text
            # Try to load icon
            pixmap = QPixmap(article.local_path)
            if not pixmap.isNull():
                item.setIcon(QIcon(pixmap))
            item.setData(Qt.UserRole, article)
            self.asset_list.addItem(item)

    def on_asset_clicked(self, item):
        article = item.data(Qt.UserRole)
        self.canvas.update_article(article)

    def save_character(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Character", "", "PNG Images (*.png)")
        if file_path:
            self.canvas.save_image(file_path)
