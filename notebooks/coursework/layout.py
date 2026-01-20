import enum
import json
from dataclasses import dataclass
from typing import Any


Cell = tuple[int, int]
RoadEdge = tuple[Cell, Cell]

class CellType(enum.StrEnum):
    H20 = "low density housing"
    H30 = "medium density housing"
    H40 = "high density housing"
    EC = "potential energy centre"
    H = "hospital"
    SC = "shopping centre"
    SCH = "school"
    OF = "office"
    O = "open space"
    G = "green space"

@dataclass
class TownLayout:
    grid_layout: list[list[str]]
    road_edges: list[RoadEdge]
    buildings: list[dict[str, Any]]
    cells: list[Cell]
    energy_center_cells: list[Cell]


def _build_town_layout(grid_layout):
    merge_types = {"H", "OF", "SCH", "SC"}
    town_layout = []
    visited = set()
    max_y = len(grid_layout)

    for y_index, row in enumerate(grid_layout):
        for x_index, cell in enumerate(row):
            if cell in merge_types:
                if (x_index, y_index) in visited:
                    continue

                stack = [(x_index, y_index)]
                visited.add((x_index, y_index))
                component = []

                while stack:
                    x_cell, y_cell = stack.pop()
                    component.append((x_cell, y_cell))
                    neighbors = (
                        (x_cell - 1, y_cell),
                        (x_cell + 1, y_cell),
                        (x_cell, y_cell - 1),
                        (x_cell, y_cell + 1),
                    )
                    for x_next, y_next in neighbors:
                        if not (0 <= y_next < max_y):
                            continue
                        if not (0 <= x_next < len(grid_layout[y_next])):
                            continue
                        if (x_next, y_next) in visited:
                            continue
                        if grid_layout[y_next][x_next] != cell:
                            continue
                        visited.add((x_next, y_next))
                        stack.append((x_next, y_next))

                x_min = min(x for x, _ in component)
                x_max = max(x for x, _ in component) + 1
                y_min = min(y for _, y in component)
                y_max = max(y for _, y in component) + 1
                town_layout.append(
                    {
                        "x_min": x_min,
                        "x_max": x_max,
                        "y_min": y_min,
                        "y_max": y_max,
                        "type": CellType[cell],
                    }
                )
            else:
                town_layout.append(
                    {
                        "x_min": x_index,
                        "x_max": x_index + 1,
                        "y_min": y_index,
                        "y_max": y_index + 1,
                        "type": CellType[cell],
                    }
                )
    return town_layout


def load_layout(layout_path):
    with layout_path.open() as handle:
        layout_data = json.load(handle)
    grid_layout = layout_data["grid_layout"]
    road_edges = [
        (tuple(edge[0]), tuple(edge[1]))
        for edge in layout_data["road_edges"]
    ]
    buildings = _build_town_layout(grid_layout)
    cells = [
        (x_index, y_index)
        for y_index, row in enumerate(grid_layout)
        for x_index, _ in enumerate(row)
    ]
    energy_center_cells = [
        (x_index, y_index)
        for y_index, row in enumerate(grid_layout)
        for x_index, cell in enumerate(row)
        if cell == CellType.EC.name
    ]
    return TownLayout(
        grid_layout=grid_layout,
        road_edges=road_edges,
        buildings=buildings,
        cells=cells,
        energy_center_cells=energy_center_cells,
    )
