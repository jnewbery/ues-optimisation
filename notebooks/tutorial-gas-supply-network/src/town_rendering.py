from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TownLayout = list[list[str]]


def render_town_layout(
    layout: TownLayout,
    image_dir: Path,
    cell_size: int = 96,
    padding: int = 24,
) -> Image.Image:
    rows = len(layout)
    cols = max(len(row) for row in layout)
    width = cols * cell_size + padding * 2
    height = rows * cell_size + padding * 2

    background = (245, 245, 245)
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", int(cell_size * 0.25))
    except OSError:
        font = ImageFont.load_default()

    color_map = {
        "20": (255, 178, 220),
        "30": (255, 0, 255),
        "40": (220, 25, 25),
        "G": (196, 234, 214),
        "EC": (20, 20, 20),
        "O": (192, 192, 192),
        "H": (0, 204, 255),
        "SC": (255, 204, 0),
        "SCH": (160, 70, 20),
        "OF": (255, 255, 0),
    }
    text_color_map = {
        "EC": (255, 255, 255),
        "SCH": (20, 20, 20),
        "OF": (20, 20, 20),
    }
    default_text_color = (25, 25, 25)

    icon_map = {
        "20": "housing-low-density.png",
        "30": "housing-med-density.png",
        "40": "housing-high-density.png",
        "EC": "energy-centre.png",
        "H": "hospital.png",
        "SC": "shopping_centre.png",
        "SCH": "school.png",
        "OF": "office.png",
    }

    loaded_icons: dict[str, Image.Image] = {}
    for key, filename in icon_map.items():
        icon_path = image_dir / filename
        if icon_path.exists():
            loaded_icons[key] = Image.open(icon_path).convert("RGBA")

    for row_idx, row in enumerate(layout):
        for col_idx, label in enumerate(row):
            x0 = padding + col_idx * cell_size
            y0 = padding + row_idx * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            fill_color = color_map.get(label, (220, 220, 220))
            draw.rectangle((x0, y0, x1, y1), fill=fill_color, outline=(90, 90, 90))

            icon = loaded_icons.get(label)
            if icon is not None:
                icon_size = int(cell_size * 0.7)
                resized = icon.resize((icon_size, icon_size), Image.LANCZOS)
                icon_x = int(x0 + (cell_size - icon_size) / 2)
                icon_y = int(y0 + (cell_size - icon_size) / 2)
                image.paste(resized, (icon_x, icon_y), resized)

            text_color = text_color_map.get(label, default_text_color)
            text_width = draw.textlength(label, font=font)
            text_height = font.getbbox(label)[3]
            text_x = x0 + (cell_size - text_width) / 2
            text_y = y0 + (cell_size - text_height) / 2
            draw.text((text_x, text_y), label, fill=text_color, font=font)

    return image
