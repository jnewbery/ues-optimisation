import enum
import json
from dataclasses import dataclass
from typing import Any
from pathlib import Path


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
    road_adjacent_cells: set[Cell]


def _build_town_layout(grid_layout: list[list[str]]) -> list[dict[str, Any]]:
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


def _build_road_adjacent_cells(
    road_edges: list[RoadEdge],
    cell_set: set[Cell],
) -> set[Cell]:
    road_adjacent_cells: set[Cell] = set()
    for (x1, y1), (x2, y2) in road_edges:
        if x1 == x2 and abs(y1 - y2) == 1:
            y_min = min(y1, y2)
            candidates = [(x1 - 1, y_min), (x1, y_min)]
        elif y1 == y2 and abs(x1 - x2) == 1:
            x_min = min(x1, x2)
            candidates = [(x_min, y1 - 1), (x_min, y1)]
        else:
            continue
        for cell in candidates:
            if cell in cell_set:
                road_adjacent_cells.add(cell)
    return road_adjacent_cells


def load_layout(layout_path: Path) -> TownLayout:
    with layout_path.open() as handle:
        layout_data = json.load(handle)
    grid_layout: list[list[str]] = layout_data["grid_layout"]
    road_edges = [
        (tuple(edge[0]), tuple(edge[1]))
        for edge in layout_data["road_edges"]
    ]
    buildings = _build_town_layout(grid_layout)
    cells: list[Cell] = [
        (x_index, y_index)
        for y_index, row in enumerate(grid_layout)
        for x_index, _ in enumerate(row)
    ]
    cell_set = set(cells)
    energy_center_cells: list[Cell] = [
        (x_index, y_index)
        for y_index, row in enumerate(grid_layout)
        for x_index, cell in enumerate(row)
        if cell == CellType.EC.name
    ]
    road_adjacent_cells = _build_road_adjacent_cells(road_edges, cell_set)
    return TownLayout(
        grid_layout=grid_layout,
        road_edges=road_edges,
        buildings=buildings,
        cells=cells,
        energy_center_cells=energy_center_cells,
        road_adjacent_cells=road_adjacent_cells,
    )
