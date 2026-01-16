from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from src.gas_network_model import GasNetworkData


def build_solution_grid(cells, values, fill_value=0.0):
    rows = []
    for i in cells:
        row = {"from": i}
        for j in cells:
            row[j] = values.get((i, j), fill_value)
        rows.append(row)
    return rows


def render_network_diagram(data: GasNetworkData, result: dict):
    cell_color = (120, 236, 140)
    cell_border = (60, 160, 90)
    pipeline_color = (28, 63, 170)
    ship_border = (58, 191, 255)
    background = (240, 248, 255)
    text_color = (25, 35, 45)

    unique_x = sorted({data.cells[cell].x_coord for cell in data.cells})
    unique_y = sorted({data.cells[cell].y_coord for cell in data.cells})
    min_step_x = min(
        (b - a for a, b in zip(unique_x, unique_x[1:]) if b > a),
        default=1.0,
    )
    min_step_y = min(
        (b - a for a, b in zip(unique_y, unique_y[1:]) if b > a),
        default=1.0,
    )
    base_step = min(min_step_x, min_step_y)

    spacing = 90
    padding = 50
    cell_size = 64

    min_x = min(unique_x)
    max_x = max(unique_x)
    min_y = min(unique_y)
    max_y = max(unique_y)
    width = int((max_x - min_x) / base_step * spacing + padding * 2 + cell_size)
    height = int((max_y - min_y) / base_step * spacing + padding * 2 + cell_size)

    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    positions = {}
    for cell in data.cells:
        x = (data.cells[cell].x_coord - min_x) / base_step * spacing + padding
        y = (max_y - data.cells[cell].y_coord) / base_step * spacing + padding
        positions[cell] = (x + cell_size / 2, y + cell_size / 2)

    active_flows = [
        result["flow"].get((i, j), 0.0)
        for i, j in result["pipe_binary"]
        if result["pipe_binary"][(i, j)] > 0.5
        and result["flow"].get((i, j), 0.0) > 0
    ]
    max_flow = max(active_flows, default=0.0)
    min_line_width = 2
    max_line_width = 10

    for i, j in result["pipe_binary"]:
        if result["pipe_binary"][(i, j)] <= 0.5:
            continue
        flow_value = result["flow"].get((i, j), 0.0)
        if flow_value <= 0:
            continue
        if max_flow > 0:
            line_width = min_line_width + (
                flow_value / max_flow * (max_line_width - min_line_width)
            )
        else:
            line_width = min_line_width
        start = positions[i]
        end = positions[j]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = (dx**2 + dy**2) ** 0.5
        if distance == 0:
            continue
        shrink = cell_size * 0.45
        sx = start[0] + dx / distance * shrink
        sy = start[1] + dy / distance * shrink
        ex = end[0] - dx / distance * shrink
        ey = end[1] - dy / distance * shrink
        draw.line(
            (sx, sy, ex, ey), fill=pipeline_color, width=int(round(line_width))
        )

        arrow_size = 10 + line_width * 0.6
        left = (
            ex - dx / distance * arrow_size - dy / distance * arrow_size * 0.6,
            ey - dy / distance * arrow_size + dx / distance * arrow_size * 0.6,
        )
        right = (
            ex - dx / distance * arrow_size + dy / distance * arrow_size * 0.6,
            ey - dy / distance * arrow_size - dx / distance * arrow_size * 0.6,
        )
        draw.polygon([left, (ex, ey), right], fill=pipeline_color)

    for cell in data.cells:
        x = (data.cells[cell].x_coord - min_x) / base_step * spacing + padding
        y = (max_y - data.cells[cell].y_coord) / base_step * spacing + padding
        rect = (x, y, x + cell_size, y + cell_size)
        radius = 12
        draw.rounded_rectangle(
            rect, radius=radius, fill=cell_color, outline=cell_border, width=3
        )
        if data.cells[cell].ship_accessible:
            draw.rounded_rectangle(rect, radius=radius, outline=ship_border, width=3)
        label = cell.replace("c", "")
        text_width = draw.textlength(label, font=font)
        draw.text(
            (x + cell_size / 2 - text_width / 2, y + cell_size / 2 - 6),
            label,
            fill=text_color,
            font=font,
        )

    return image
