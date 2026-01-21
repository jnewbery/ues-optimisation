import math
from typing import Any, Sequence

from ortools.linear_solver import pywraplp

from constants import DEMAND
from layout import TownLayout


def _map_center(town: TownLayout) -> tuple[float, float]:
    max_x = max(x for x, _ in town.cells)
    max_y = max(y for _, y in town.cells)
    return max_x / 2, max_y / 2


def _pick_representative_cell(
    *,
    footprint: Sequence[tuple[int, int]],
    road_cells: set[tuple[int, int]],
    center: tuple[float, float],
) -> tuple[int, int]:
    candidates = [cell for cell in footprint if cell in road_cells]
    if not candidates:
        candidates = list(footprint)
    center_x, center_y = center
    return min(
        candidates,
        key=lambda cell: (
            (cell[0] - center_x) ** 2 + (cell[1] - center_y) ** 2,
            cell[0],
            cell[1],
        ),
    )


def build_cell_demand_summary(town: TownLayout) -> list[dict[str, Any]]:
    cell_set = set(town.cells)
    road_cells = {cell for edge in town.road_edges for cell in edge}
    center = _map_center(town)
    cell_summaries = []
    for building_index, building in enumerate(town.buildings):
        building_type = building["type"]
        demand = DEMAND.get(building_type.name)
        if demand is None:
            continue
        footprint = [
            (x_cell, y_cell)
            for x_cell in range(building["x_min"], building["x_max"])
            for y_cell in range(building["y_min"], building["y_max"])
            if (x_cell, y_cell) in cell_set
        ]
        if not footprint:
            continue
        winter_thermal = demand.thermal_demand_kwh_year * demand.thermal_winter_factor
        representative_cell = _pick_representative_cell(
            footprint=footprint,
            road_cells=road_cells,
            center=center,
        )
        cell_summaries.append(
            {
                "id": building_index,
                "type": building_type.value,
                "demand": winter_thermal,
                "cell": representative_cell,
                "footprint": footprint,
            }
        )
    return cell_summaries


def build_cell_demands(
    town: TownLayout,
) -> dict[tuple[int, int], float]:
    cell_summaries = build_cell_demand_summary(town)
    cell_demands: dict[tuple[int, int], float] = {}
    for summary in cell_summaries:
        cell = summary["cell"]
        cell_demands[cell] = cell_demands.get(cell, 0.0) + summary["demand"]
    return cell_demands


def build_and_solve_model(
    town: TownLayout,
    *,
    cost_energy_center: float,
    cost_pipe: float,
    cell_demands: dict[tuple[int, int], float] | None = None,
) -> dict[str, Any]:
    # Allow cell demands to be overridden by calling function
    if cell_demands is None:
        cell_demands = build_cell_demands(town)

    total_demand = sum(cell_demands.values())
    if total_demand == 0:
        return {
            "status": "no-demand",
            "objective_value": 0.0,
            "energy_edges": [],
            "pipe_binary": {},
            "energy_centers": [],
        }

    # Build edges between neighboring cells
    neighbor_deltas = [
        (dx, dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if not (dx == 0 and dy == 0)
    ]
    edges = []
    neighbors_by_cell = {_cell: [] for _cell in town.cells}
    cell_set = set(town.cells)
    for x_cell, y_cell in town.cells:
        for dx, dy in neighbor_deltas:
            nx = x_cell + dx
            ny = y_cell + dy
            if (nx, ny) not in cell_set:
                continue
            neighbors_by_cell[(x_cell, y_cell)].append((nx, ny))
            if (x_cell, y_cell) < (nx, ny):
                edges.append(((x_cell, y_cell), (nx, ny)))

    solver = pywraplp.Solver.CreateSolver("CBC_MIXED_INTEGER_PROGRAMMING")
    if solver is None:
        raise RuntimeError("Failed to create OR-Tools solver.")

    # Decision variables
    pipe_binary = {(i, j): solver.BoolVar(f"pipe[{i},{j}]") for i, j in edges}
    directed_edges = []
    for i, j in edges:
        directed_edges.append((i, j))
        directed_edges.append((j, i))
    parent = {(i, j): solver.BoolVar(f"parent[{i},{j}]") for i, j in directed_edges}
    active_cell = {cell: solver.BoolVar(f"active[{cell}]") for cell in town.cells}
    depth = {
        cell: solver.IntVar(0, len(town.cells), f"depth[{cell}]")
        for cell in town.cells
    }
    build_center = {
        cell: solver.BoolVar(f"build_ec[{cell}]")
        for cell in town.energy_center_cells
    }

    # Constraints
    big_m = len(town.cells)
    for i, j in edges:
        solver.Add(parent[(i, j)] + parent[(j, i)] <= pipe_binary[(i, j)])
        solver.Add(active_cell[i] >= pipe_binary[(i, j)])
        solver.Add(active_cell[j] >= pipe_binary[(i, j)])

    for cell in town.cells:
        if cell_demands.get(cell, 0.0) > 0:
            solver.Add(active_cell[cell] == 1)
        solver.Add(active_cell[cell] >= build_center.get(cell, 0.0))

    for cell in town.cells:
        incoming = [
            parent[(neighbor, cell)]
            for neighbor in neighbors_by_cell[cell]
        ]
        if incoming:
            solver.Add(
                solver.Sum(incoming) == active_cell[cell] - build_center.get(cell, 0.0)
            )
        else:
            solver.Add(active_cell[cell] == build_center.get(cell, 0.0))

        solver.Add(depth[cell] <= big_m * active_cell[cell])
        solver.Add(depth[cell] >= active_cell[cell] - big_m * build_center.get(cell, 0.0))
        solver.Add(depth[cell] <= big_m * (1 - build_center.get(cell, 0.0)))

    for i, j in directed_edges:
        solver.Add(
            depth[j] >= depth[i] + 1 - big_m * (1 - parent[(i, j)])
        )

    # Objective function
    objective_terms = []
    for (i, j), var in pipe_binary.items():
        dx = i[0] - j[0]
        dy = i[1] - j[1]
        length = math.sqrt(dx * dx + dy * dy)
        objective_terms.append(var * cost_pipe * length)
    objective_terms.extend(
        build_center[cell] * cost_energy_center
        for cell in town.energy_center_cells
    )

    # Solve
    solver.Minimize(solver.Sum(objective_terms))
    status = solver.Solve()

    # Extract results
    pipe_binary_values = {edge: pipe_binary[edge].solution_value() for edge in pipe_binary}
    energy_edges = []
    for (i, j), value in pipe_binary_values.items():
        if value <= 0.5:
            continue
        energy_edges.append((i[0] + 0.5, i[1] + 0.5, j[0] + 0.5, j[1] + 0.5))
    energy_centers = []
    if status == pywraplp.Solver.OPTIMAL:
        for cell, var in build_center.items():
            if var.solution_value() > 0.5:
                energy_centers.append(cell)

    return {
        "status": status,
        "objective_value": solver.Objective().Value()
        if status == pywraplp.Solver.OPTIMAL
        else None,
        "energy_edges": energy_edges,
        "pipe_binary": pipe_binary_values,
        "energy_centers": energy_centers,
    }
