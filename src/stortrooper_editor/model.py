# Copyright (c) 2025 Ricardo Quesada

import glob
import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Article:
    id: str
    image_name: str
    category: str
    layer_name: str
    x: int
    y: int
    wearing: str  # "-1" or other values, might use for defaults
    local_path: str = ""


class CharacterData:
    @staticmethod
    def get_available_article_files(res_path: str, char_name: str) -> List[str]:
        path = os.path.join(res_path, char_name)
        if not os.path.exists(path):
            return []
        files = glob.glob(os.path.join(path, "articles*.txt"))
        return sorted([os.path.basename(f) for f in files])

    def __init__(
        self, name: str, res_path: str, articles_filename: str = "articles.txt"
    ):
        self.name = name
        self.root_path = os.path.join(res_path, name)
        self.articles_filename = articles_filename
        self.articles: List[Article] = []
        self.categories: Dict[str, List[Article]] = {}
        # Default layer order based on config.txt observation, can be refined
        self.layer_order = [
            "behind",
            "body",
            "hair",
            "underware",
            "tops",
            "shoes",
            "bottoms",
            "jackets",
            "hats",
            "infront",
        ]
        # Map layer names to z-index (index in the list)
        self.layer_z_index = {name: i for i, name in enumerate(self.layer_order)}

    def load(self):
        articles_path = os.path.join(self.root_path, self.articles_filename)
        if not os.path.exists(articles_path):
            print(f"Warning: {articles_path} not found")
            return

        with open(articles_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Simple parsing state machine
        in_data = False
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "HCDataSetFile_data" in line:
                in_data = True
                continue

            if in_data:
                # Format: "id" "imageName" "category" "layer" "snapPosX" "snapPosY" "wearing" ...
                # We need to split by quotes.
                # Example: "10" "boy_body_02.gif" "body" "body" "26" "28" "-1"
                parts = [p for p in line.split('"') if p.strip()]
                if len(parts) >= 7:
                    art_id = parts[0]
                    img_name = parts[1]
                    category = parts[2]
                    layer = parts[3]
                    try:
                        x = int(parts[4])
                        y = int(parts[5])
                    except ValueError:
                        x = 0
                        y = 0
                    wearing = parts[6]

                    # Filter out "brazos_arriba" or similar variants if they are not the main pose
                    # Actually, usually "wearing" being "-1" means it's an inventory item?
                    # And "0" might be a default or alternative pose.
                    # Looking at the file:
                    # "10" "boy_body_02.gif" ... "-1"
                    # "10" "boy_body_02_brazos_arriba.gif" ... "0"
                    # So we probably only want the ones with "-1" or items that look "normal".
                    # Let's filter out files ending in _brazos_arriba.gif for now to keep it simple

                    if "_brazos_arriba" in img_name:
                        continue

                    # Construct local path
                    # Images seem to be in 'data' subdir based on listing
                    # But wait, looking at file list:
                    # src/res/boy/data/boy_body_02.gif
                    # AND
                    # src/res/boy/data/images/ ? No, the list_dir showed files directly in data/
                    # Let's check where the file actually is.
                    # Previous list_dir of src/res/boy/data showed 165 files, mostly gifs.
                    # so path is res_path/name/data/img_name

                    img_path = os.path.join(self.root_path, "data", img_name)

                    # Some files might simply not exist or be in a subdir?
                    # The listing showed flat structure in `data/`.

                    article = Article(
                        id=art_id,
                        image_name=img_name,
                        category=category,
                        layer_name=layer,
                        x=x,
                        y=y,
                        wearing=wearing,
                        local_path=img_path,
                    )

                    self.articles.append(article)

                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append(article)

        print(f"Loaded {len(self.articles)} articles for {self.name}")

    def get_article_z_index(self, article: Article) -> int:
        return self.layer_z_index.get(article.layer_name, 0)
