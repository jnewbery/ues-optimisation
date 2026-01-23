from pathlib import Path
from typing import TypedDict

from PIL import Image, ImageDraw, ImageFont


class Building(TypedDict):
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    building_type: str


TownLayout = list[Building]

def render_town_layout(
    layout: TownLayout,
    image_dir: Path,
    cell_size: int = 128,
    padding: int = 24,
) -> Image.Image:
    max_x = max(building["x_max"] for building in layout)
    max_y = max(building["y_max"] for building in layout)
    width = max_x * cell_size + padding * 2
    height = max_y * cell_size + padding * 2

    background = (245, 245, 245)
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", int(cell_size * 0.25))
    except OSError:
        font = ImageFont.load_default()

    color_map = {
        "low density housing": (255, 178, 220),
        "medium density housing": (255, 0, 255),
        "high density housing": (220, 25, 25),
        "green space": (20, 163, 58),
        "potential energy centre location": (100, 100, 100),
        "other": (192, 192, 192),
        "hospital": (0, 204, 255),
        "shopping centre": (255, 204, 0),
        "school": (160, 70, 20),
        "office": (255, 255, 0),
    }

    icon_map = {
        "low density housing": "housing-low-density.png",
        "medium density housing": "housing-med-density.png",
        "high density housing": "housing-high-density.png",
        "potential energy centre location": "energy-centre.png",
        "hospital": "hospital.png",
        "shopping centre": "shopping-centre.png",
        "school": "school.png",
        "office": "office.png",
        "green space": "green-space.png",
        "open space": "open-space.png",
    }

    loaded_icons: dict[str, Image.Image] = {}
    for key, filename in icon_map.items():
        icon_path = image_dir / filename
        if icon_path.exists():
            loaded_icons[key] = Image.open(icon_path).convert("RGBA")

    for building in layout:
        building_type = building["building_type"]
        x0 = padding + building["x_min"] * cell_size
        y0 = padding + building["y_min"] * cell_size
        x1 = padding + building["x_max"] * cell_size
        y1 = padding + building["y_max"] * cell_size
        fill_color = color_map.get(building_type, (220, 220, 220))
        draw.rectangle((x0, y0, x1, y1), fill=fill_color, outline=(90, 90, 90))

        icon = loaded_icons.get(building_type)
        if icon is not None:
            icon_size = int(cell_size * 0.7)
            resized = icon.resize((icon_size, icon_size), Image.LANCZOS)
            icon_x = int(x0 + (x1 - x0 - icon_size) / 2)
            icon_y = int(y0 + (cell_size - icon_size) / 2)
            image.paste(resized, (icon_x, icon_y), resized)

        # label = label_map.get(building_type, building_type)
        # text_color = text_color_map.get(building_type, default_text_color)
        # text_width = draw.textlength(label, font=font)
        # text_height = font.getbbox(label)[3]
        # text_x = x0 + (x1 - x0 - text_width) / 2
        # text_y = y0 + (y1 - y0 - text_height) / 2
        # draw.text((text_x, text_y), label, fill=text_color, font=font)

    return image
