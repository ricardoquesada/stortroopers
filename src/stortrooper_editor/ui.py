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
            self.scene.removeItem(self.pixmap_items[article.layer_name])
            del self.pixmap_items[article.layer_name]
            del self.active_articles[article.layer_name]
        
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

    def remove_article(self, article: Article):
        if article.layer_name in self.pixmap_items:
            # Check if it is indeed this article
            current_article = self.active_articles.get(article.layer_name)
            if current_article and current_article.id == article.id:
                self.scene.removeItem(self.pixmap_items[article.layer_name])
                del self.pixmap_items[article.layer_name]
                del self.active_articles[article.layer_name]

    def is_article_active(self, article: Article) -> bool:
        current_article = self.active_articles.get(article.layer_name)
        return current_article is not None and current_article.id == article.id

    def set_zoom(self, scale):
        self.resetTransform()
        self.scale(scale, scale)

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
        self.setIconSize(QSize(128, 128))
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(10)

class MainWindow(QMainWindow):
    def __init__(self, res_path):
        super().__init__()
        self.setWindowTitle("StorTrooper Character Editor")
        self.resize(1000, 700)
        self.res_path = res_path
        self.current_char_data = None
        self.current_zoom = 4.0
        
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
        self.char_combo.currentIndexChanged.connect(self.on_character_changed)
        left_layout.addWidget(QLabel("Character Type:"))
        left_layout.addWidget(self.char_combo)

        # Articles File Selector
        self.articles_combo = QComboBox()
        self.articles_combo.currentIndexChanged.connect(self.reload_data)
        left_layout.addWidget(QLabel("Articles File:"))
        left_layout.addWidget(self.articles_combo)
        
        # Category Tabs
        self.category_tabs = QTabWidget()
        self.category_tabs.currentChanged.connect(self.on_category_changed)
        left_layout.addWidget(self.category_tabs)
        
        # Asset List
        self.asset_list = AssetSelector()
        self.asset_list.itemClicked.connect(self.on_asset_clicked)
        self.asset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.asset_list.customContextMenuRequested.connect(self.on_asset_list_context_menu)
        left_layout.addWidget(self.asset_list)
        
        # Save Button
        save_btn = QPushButton("Save Character to PNG")
        save_btn.clicked.connect(self.save_character)
        left_layout.addWidget(save_btn)

        # Right Panel: Canvas
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, 2)
        
        # Zoom Controls
        zoom_layout = QHBoxLayout()
        zoom_in_btn = QPushButton("Zoom In (+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn = QPushButton("Zoom Out (-)")
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        zoom_layout.addWidget(zoom_in_btn)
        right_layout.addLayout(zoom_layout)
        
        self.canvas = CanvasWidget()
        right_layout.addWidget(self.canvas)
        
        # Set default zoom
        self.canvas.set_zoom(self.current_zoom)
        
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

    def on_character_changed(self):
        char_name = self.char_combo.currentText()
        if not char_name:
            return
            
        # Update articles combo
        self.articles_combo.blockSignals(True)
        self.articles_combo.clear()
        
        files = CharacterData.get_available_article_files(self.res_path, char_name)
        self.articles_combo.addItems(files)
        
        # Select "articles.txt" if present, else first one
        index = self.articles_combo.findText("articles.txt")
        if index >= 0:
            self.articles_combo.setCurrentIndex(index)
        elif self.articles_combo.count() > 0:
            self.articles_combo.setCurrentIndex(0)
            
        self.articles_combo.blockSignals(False)
        self.reload_data()

    def reload_data(self):
        char_name = self.char_combo.currentText()
        if not char_name:
            return
            
        articles_file = self.articles_combo.currentText()
        # If no articles file found, we can't load much, but let's try with default
        if not articles_file:
             articles_file = "articles.txt"

        self.current_char_data = CharacterData(char_name, self.res_path, articles_filename=articles_file)
        self.current_char_data.load()
        
        self.canvas.set_character(self.current_char_data)
        
        # Update Categories
        self.category_tabs.blockSignals(True) # Avoid triggering multiple updates
        self.category_tabs.clear()
        
        # Define a consistent order if possible, or alphabetical
        categories = sorted(list(self.current_char_data.categories.keys()))
        
        # Prioritize body/skin
        if "body" in categories:
            categories.insert(0, categories.pop(categories.index("body")))
            
        for cat in categories:
            self.category_tabs.addTab(QWidget(), cat)
        
        self.category_tabs.blockSignals(False)
            
        if self.category_tabs.count() > 0:
            self.on_category_changed(0)
            
        # Try to set default body if available
        if "body" in self.current_char_data.categories:
             # Just pick the first body
             first_body = self.current_char_data.categories["body"][0]
             self.canvas.update_article(first_body)
             # Update visual feedback after loading default body
             self.update_asset_list_visuals()

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
        
        self.update_asset_list_visuals()

    def update_asset_list_visuals(self):
        # Iterate over all items in the list widget and check if they are active
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            article = item.data(Qt.UserRole)
            if self.canvas.is_article_active(article):
                item.setBackground(Qt.cyan)  # Highlight color
            else:
                item.setBackground(Qt.NoBrush) # Reset color

    def on_asset_clicked(self, item):
        article = item.data(Qt.UserRole)
        self.canvas.update_article(article)
        self.update_asset_list_visuals()

    def on_asset_list_context_menu(self, position):
        item = self.asset_list.itemAt(position)
        if item:
            article = item.data(Qt.UserRole)
            if self.canvas.is_article_active(article):
                self.canvas.remove_article(article)
                self.update_asset_list_visuals()

    def save_character(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Character", "", "PNG Images (*.png)")
        if file_path:
            self.canvas.save_image(file_path)

    def zoom_in(self):
        self.current_zoom += 0.5
        self.canvas.set_zoom(self.current_zoom)

    def zoom_out(self):
        if self.current_zoom > 0.5:
            self.current_zoom -= 0.5
            self.canvas.set_zoom(self.current_zoom)
