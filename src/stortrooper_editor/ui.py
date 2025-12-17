# Copyright (c) 2025 Ricardo Quesada

import json
import logging
import os
import random

from PySide6.QtCore import QRectF, QSettings, QSize, Qt
from PySide6.QtGui import QAction, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFileDialog,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMdiArea,
    QMdiSubWindow,
    QMessageBox,
    QPushButton,
    QStyle,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .model import Article, CharacterData


class CanvasWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing, False)  # Pixel art, keep it sharp?
        self.setRenderHint(QPainter.SmoothPixmapTransform, False)
        # Fixed size for scene, maybe? Or dynamic?
        # The coordinates in articles.txt seem to operate in a specific space.
        # Let's assume a reasonable canvas size, maybe 400x400 or just enough to fit.
        # Based on coords like y=128 for shoes, it's not huge.
        self.scene.setSceneRect(0, 0, 300, 300)
        self.active_articles = {}  # layer_name -> Article
        self.pixmap_items = {}  # layer_name -> QGraphicsPixmapItem
        self.current_zoom = 4.0
        self.project_file_path = None

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
            logging.error(f"Failed to load image: {article.local_path}")
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
        self.current_zoom = scale
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
        self.resize(1200, 800)
        self.res_path = res_path

        # Settings
        self.settings = QSettings("RetroMoe", "StorTrooperEditor")

        # Central Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.currentChanged.connect(self.update_ui_from_active_tab)
        self.tab_widget.tabCloseRequested.connect(self.on_tab_close_requested)
        self.setCentralWidget(self.tab_widget)

        # Dock Widget for Tools
        self.create_tools_dock()

        # Menu Bar
        self.create_menu_bar()

        # Populate Characters
        self.populate_characters()

        # Restore UI Session
        self.restore_ui_session()

        # Restore Session or New Document
        self.restore_last_session()

    def closeEvent(self, event):
        # Save open documents to session
        open_files = []
        for i in range(self.tab_widget.count()):
            canvas = self.tab_widget.widget(i)
            if isinstance(canvas, CanvasWidget) and canvas.project_file_path:
                open_files.append(canvas.project_file_path)

        self.settings.setValue("last_session_files", open_files)
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())
        event.accept()

    def restore_last_session(self):
        last_files = self.settings.value("last_session_files", [])
        # QSettings might return None or type conversion quirks, ensure list
        if not isinstance(last_files, list):
            last_files = []

        files_opened = 0
        for file_path in last_files:
            if os.path.exists(file_path):
                if self.open_project_file(file_path):
                    files_opened += 1

        if files_opened == 0:
            self.create_new_document()

    def restore_ui_session(self):
        geometry = self.settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value("window_state")
        if state:
            self.restoreState(state)

    def restore_default_layout(self):
        self.resize(1200, 800)
        # Assuming 'Tools' dock is the only one for now
        dock = self.findChild(QDockWidget, "ToolsDock")
        if dock:
            self.addDockWidget(Qt.RightDockWidgetArea, dock)
            dock.setFloating(False)
            dock.show()
        
        if hasattr(self, "main_toolbar") and self.main_toolbar:
            logging.info("Restoring toolbar visibility and position")
            self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)
            self.main_toolbar.setVisible(True)
            if not self.main_toolbar.toggleViewAction().isChecked():
                self.main_toolbar.toggleViewAction().trigger()

    def create_tools_dock(self):
        dock = QDockWidget("Tools", self)
        dock.setObjectName("ToolsDock")
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Character Selector
        self.char_combo = QComboBox()
        self.char_combo.currentIndexChanged.connect(self.on_character_changed)
        layout.addWidget(QLabel("Character Type:"))
        layout.addWidget(self.char_combo)

        # Articles File Selector
        self.articles_combo = QComboBox()
        self.articles_combo.currentIndexChanged.connect(self.reload_data)
        layout.addWidget(QLabel("Articles File:"))
        layout.addWidget(self.articles_combo)

        # Category Tabs
        self.category_tabs = QTabWidget()
        self.category_tabs.currentChanged.connect(self.on_category_changed)
        layout.addWidget(self.category_tabs)

        # Asset List
        self.asset_list = AssetSelector()
        self.asset_list.itemClicked.connect(self.on_asset_clicked)
        self.asset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.asset_list.customContextMenuRequested.connect(
            self.on_asset_list_context_menu
        )
        layout.addWidget(self.asset_list)




        # Zoom Controls
        zoom_layout = QHBoxLayout()
        zoom_in_btn = QPushButton("Zoom In (+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn = QPushButton("Zoom Out (-)")
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        zoom_layout.addWidget(zoom_in_btn)
        layout.addLayout(zoom_layout)

        dock.setWidget(panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def create_menu_bar(self):
        menubar = self.menuBar()
        self.main_toolbar = self.addToolBar("Main Toolbar")
        self.main_toolbar.setObjectName("MainToolbar")
        style = self.style()

        # File Menu
        file_menu = menubar.addMenu("File")

        new_action = file_menu.addAction("New Project")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.create_new_document)

        open_action = file_menu.addAction("Open Project...")
        open_action.setShortcut("Ctrl+O")
        open_action.setIcon(QIcon.fromTheme("document-open", style.standardIcon(QStyle.SP_DialogOpenButton)))
        open_action.triggered.connect(self.open_project)
        self.main_toolbar.addAction(open_action)

        # Recent Files
        self.recent_menu = file_menu.addMenu("Open Recent")
        self.update_recent_menu()

        # Save Action
        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.setIcon(QIcon.fromTheme("document-save", style.standardIcon(QStyle.SP_DialogSaveButton)))
        save_action.triggered.connect(self.save_project)
        self.main_toolbar.addAction(save_action)

        save_as_action = file_menu.addAction("Save As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        # Reuse save icon for now
        save_as_action.setIcon(QIcon.fromTheme("document-save-as", style.standardIcon(QStyle.SP_DialogSaveButton)))
        save_as_action.triggered.connect(self.save_project_as)
        self.main_toolbar.addAction(save_as_action)

        file_menu.addSeparator()

        export_action = file_menu.addAction("Export to PNG...")
        export_action.setShortcut("Ctrl+E")
        export_action.setIcon(QIcon.fromTheme("document-export", style.standardIcon(QStyle.SP_DialogApplyButton)))
        export_action.triggered.connect(self.save_character)
        self.main_toolbar.addAction(export_action)
        
        # Random Action
        random_action = QAction("Random", self)
        random_action.setIcon(QIcon.fromTheme("media-playlist-shuffle", style.standardIcon(QStyle.SP_BrowserReload)))
        random_action.triggered.connect(self.randomize_character)
        self.main_toolbar.addAction(random_action)

        # Window Menu
        window_menu = menubar.addMenu("Window")

        close_action = window_menu.addAction("Close Tab")
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_current_tab)

        window_menu.addSeparator()

        restore_layout_action = window_menu.addAction("Restore Default Layout")
        restore_layout_action.triggered.connect(self.restore_default_layout)

    def update_recent_menu(self):
        self.recent_menu.clear()
        recent_files = self.settings.value("recent_files", [])
        if not isinstance(recent_files, list):
            recent_files = []

        for file_path in recent_files:
            action = QAction(os.path.basename(file_path), self)
            action.setData(file_path)
            action.triggered.connect(
                lambda checked=False, path=file_path: self.open_project_file(path)
            )
            self.recent_menu.addAction(action)

        if not recent_files:
            self.recent_menu.setDisabled(True)
        else:
            self.recent_menu.setEnabled(True)

    def add_recent_file(self, file_path):
        recent_files = self.settings.value("recent_files", [])
        if not isinstance(recent_files, list):
            recent_files = []

        # Remove if exists to move to top
        if file_path in recent_files:
            recent_files.remove(file_path)

        recent_files.insert(0, file_path)

        # Limit to 10
        if len(recent_files) > 10:
            recent_files = recent_files[:10]

        self.settings.setValue("recent_files", recent_files)
        self.update_recent_menu()

    def populate_characters(self):
        if not os.path.exists(self.res_path):
            QMessageBox.critical(
                self, "Error", f"Resource path not found: {self.res_path}"
            )
            return

        chars = [
            d
            for d in os.listdir(self.res_path)
            if os.path.isdir(os.path.join(self.res_path, d))
            and d != "data"
            and not d.startswith(".")
        ]
        chars.sort()
        self.char_combo.addItems(chars)

    def create_new_document(self):
        canvas = CanvasWidget()
        canvas.set_zoom(4.0)

        index = self.tab_widget.addTab(canvas, "Untitled")
        self.tab_widget.setCurrentIndex(index)
        
        # Initialize with current selection if possible
        self.reload_data()

    def on_tab_close_requested(self, index):
        if index >= 0:
            widget = self.tab_widget.widget(index)
            # Potentially check for unsaved changes here in the future
            self.tab_widget.removeTab(index)
            widget.deleteLater()

    def close_current_tab(self):
        self.on_tab_close_requested(self.tab_widget.currentIndex())

    def get_current_canvas(self):
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, CanvasWidget):
            return widget
        return None

    def update_ui_from_active_tab(self, index):
        if index < 0:
            # Could clear UI or disable properties
            self.asset_list.clear()
            self.category_tabs.clear()
            return

        canvas = self.tab_widget.widget(index)
        if not isinstance(canvas, CanvasWidget):
            return

        # Restore UI state from this canvas
        self.char_combo.blockSignals(True)
        self.articles_combo.blockSignals(True)

        if hasattr(canvas, "character_data") and canvas.character_data:
            # Select Character
            idx = self.char_combo.findText(canvas.character_data.name)
            if idx >= 0:
                self.char_combo.setCurrentIndex(idx)

            # Update Articles Combo
            files = CharacterData.get_available_article_files(
                self.res_path, canvas.character_data.name
            )
            self.articles_combo.clear()
            self.articles_combo.addItems(files)

            idx = self.articles_combo.findText(canvas.character_data.articles_filename)
            if idx >= 0:
                self.articles_combo.setCurrentIndex(idx)

        self.char_combo.blockSignals(False)
        self.articles_combo.blockSignals(False)

        self.refresh_categories_and_assets(canvas)

    def refresh_categories_and_assets(self, canvas):
        if not hasattr(canvas, "character_data") or not canvas.character_data:
            self.category_tabs.clear()
            self.asset_list.clear()
            return

        # Store current tab text to restore it?
        current_tab_text = self.category_tabs.tabText(self.category_tabs.currentIndex())

        self.category_tabs.blockSignals(True)
        self.category_tabs.clear()

        categories = sorted(list(canvas.character_data.categories.keys()))
        if "body" in categories:
            categories.insert(0, categories.pop(categories.index("body")))

        for cat in categories:
            self.category_tabs.addTab(QWidget(), cat)

        self.category_tabs.blockSignals(False)

        # Try to restore tab or default
        idx = -1
        if current_tab_text:
            for i in range(self.category_tabs.count()):
                if self.category_tabs.tabText(i) == current_tab_text:
                    idx = i
                    break

        if idx == -1 and self.category_tabs.count() > 0:
            idx = 0

        if idx != -1:
            self.category_tabs.setCurrentIndex(idx)
            self.on_category_changed(idx)

    def on_character_changed(self):
        char_name = self.char_combo.currentText()
        if not char_name:
            return

        self.articles_combo.blockSignals(True)
        self.articles_combo.clear()
        files = CharacterData.get_available_article_files(self.res_path, char_name)
        self.articles_combo.addItems(files)

        index = self.articles_combo.findText("articles.txt")
        if index >= 0:
            self.articles_combo.setCurrentIndex(index)
        elif self.articles_combo.count() > 0:
            self.articles_combo.setCurrentIndex(0)

        self.articles_combo.blockSignals(False)

        canvas = self.get_current_canvas()
        if not canvas:
            return

        self.reload_data()

    def reload_data(self):
        canvas = self.get_current_canvas()
        if not canvas:
            return

        char_name = self.char_combo.currentText()
        articles_file = self.articles_combo.currentText()
        if not articles_file:
            logging.warning("No articles file selected, using default articles.txt")
            articles_file = "articles.txt"

        if not char_name:
            return

        # Avoid reloading if it's the same data?
        # Sometimes we want to force reload.

        char_data = CharacterData(
            char_name, self.res_path, articles_filename=articles_file
        )
        char_data.load()

        canvas.set_character(char_data)

        # Default body logic
        if "body" in char_data.categories:
            first_body = char_data.categories["body"][0]
            canvas.update_article(first_body)

        self.refresh_categories_and_assets(canvas)

    def on_category_changed(self, index):
        if index < 0:
            return

        canvas = self.get_current_canvas()
        if (
            not canvas
            or not hasattr(canvas, "character_data")
            or not canvas.character_data
        ):
            self.asset_list.clear()
            return

        cat_name = self.category_tabs.tabText(index)
        self.asset_list.clear()

        articles = canvas.character_data.categories.get(cat_name, [])
        for article in articles:
            item = QListWidgetItem(article.image_name)
            pixmap = QPixmap(article.local_path)
            if not pixmap.isNull():
                item.setIcon(QIcon(pixmap))
            item.setData(Qt.UserRole, article)
            self.asset_list.addItem(item)

        self.update_asset_list_visuals()

    def update_asset_list_visuals(self):
        canvas = self.get_current_canvas()
        if not canvas:
            return

        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            article = item.data(Qt.UserRole)
            if canvas.is_article_active(article):
                item.setBackground(Qt.cyan)
            else:
                item.setBackground(Qt.NoBrush)

    def on_asset_clicked(self, item):
        canvas = self.get_current_canvas()
        if not canvas:
            return
        article = item.data(Qt.UserRole)
        canvas.update_article(article)
        self.update_asset_list_visuals()

    def on_asset_list_context_menu(self, position):
        canvas = self.get_current_canvas()
        if not canvas:
            return
        item = self.asset_list.itemAt(position)
        if item:
            article = item.data(Qt.UserRole)
            if canvas.is_article_active(article):
                canvas.remove_article(article)
                self.update_asset_list_visuals()

    def zoom_in(self):
        canvas = self.get_current_canvas()
        if canvas:
            canvas.set_zoom(canvas.current_zoom + 0.5)

    def zoom_out(self):
        canvas = self.get_current_canvas()
        if canvas:
            canvas.set_zoom(canvas.current_zoom - 0.5)

    def save_character(self):
        canvas = self.get_current_canvas()
        if not canvas:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Character", "", "PNG Images (*.png)"
        )
        if file_path:
            canvas.save_image(file_path)

    def save_project(self):
        canvas = self.get_current_canvas()
        if not canvas or not hasattr(canvas, "character_data"):
            QMessageBox.warning(self, "Warning", "No active project to save.")
            return

        if canvas.project_file_path:
            self._save_to_file(canvas.project_file_path)
        else:
            self.save_project_as()

    def save_project_as(self):
        canvas = self.get_current_canvas()
        if not canvas or not hasattr(canvas, "character_data"):
            QMessageBox.warning(self, "Warning", "No active project to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "", "StorTrooper Project (*.stp *.json)"
        )
        if not file_path:
            return

        self._save_to_file(file_path)

    def _save_to_file(self, file_path):
        canvas = self.get_current_canvas()
        if not canvas:
            return

        active_ids = [article.id for article in canvas.active_articles.values()]

        data = {
            "character_name": canvas.character_data.name,
            "articles_file": canvas.character_data.articles_filename,
            "active_articles": active_ids,
        }

        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(
                self, "Success", f"Project saved to {os.path.basename(file_path)}"
            )
            # Update window title and path
            canvas.project_file_path = file_path
            self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(file_path))
            self.add_recent_file(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")

    def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "StorTrooper Project (*.stp *.json)"
        )
        if file_path:
            self.open_project_file(file_path)

    def open_project_file(self, file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            char_name = data.get("character_name")
            articles_file = data.get("articles_file")
            active_ids = data.get("active_articles", [])

            if not char_name or not articles_file:
                raise ValueError("Invalid project file format.")

            # New document
            self.create_new_document()
            canvas = self.get_current_canvas()
            if not canvas:
                return False

            # Manually set character to match file without relying solely on UI
            # But we must update UI too?
            # Let's verify character exists
            idx = self.char_combo.findText(char_name)
            if idx == -1:
                QMessageBox.critical(
                    self, "Error", f"Character '{char_name}' not found."
                )
                self.close_current_tab()
                return False

            # Setting index triggers on_character_changed -> reload_data -> sets default body
            self.char_combo.setCurrentIndex(idx)

            # Now update articles file if needed
            idx = self.articles_combo.findText(articles_file)
            if idx != -1:
                self.articles_combo.setCurrentIndex(idx)

            # At this point, reload_data has run and loaded the character + default body

            # Now Apply Saved Articles (Clear defaults first?)
            # Yes, if we want exact restoration.
            canvas.clear()

            # We need to make sure canvas.character_data is set (it is by reload_data)

            for art_id in active_ids:
                article = canvas.character_data.get_article_by_id(art_id)
                if article:
                    canvas.update_article(article)
                else:
                    logging.warning(f"Article {art_id} not found")

            self.update_asset_list_visuals()

            # Update window and tracking
            canvas.project_file_path = file_path
            self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(file_path))
            self.add_recent_file(file_path)
            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")
            return False

    def randomize_character(self):
        # 1. Randomize Character
        if self.char_combo.count() > 0:
            import random  # Ensure it's available or use the module level one
            # Logic to pick a random character
            # We want to allow picking the SAME character too, so we just pick any index.
            # But if we pick the same index, no signal is emitted, so we might need to manually trigger updates 
            # OR we just trust that if it's the same, we don't need to change it.
            # However, for "articles file", if we stick to the same character, we might want to change the article file.
            
            # Let's pick a random char index
            char_idx = random.randint(0, self.char_combo.count() - 1)
            self.char_combo.setCurrentIndex(char_idx)
            
            # If the index didn't change, on_character_changed wasn't called.
            # But we might still want to randomize the article file.
            
        # 2. Randomize Article File
        # The char combo change (if any) updated the articles combo.
        if self.articles_combo.count() > 0:
            art_idx = random.randint(0, self.articles_combo.count() - 1)
            self.articles_combo.setCurrentIndex(art_idx)

        # 3. Randomize Outfit
        canvas = self.get_current_canvas()
        if not canvas or not hasattr(canvas, "character_data"):
            return

        new_outfit = canvas.character_data.get_random_outfit()
        if not new_outfit:
            QMessageBox.information(self, "Info", "No articles found to randomize.")
            return

        canvas.clear()
        
        for article in new_outfit:
            canvas.update_article(article)
            
        self.update_asset_list_visuals()
