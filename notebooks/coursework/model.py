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
        total_demand = winter_thermal * len(footprint)
        representative_cell = _pick_representative_cell(
            footprint=footprint,
            road_cells=road_cells,
            center=center,
        )
        cell_summaries.append(
            {
                "id": building_index,
                "type": building_type.value,
                "demand": total_demand,
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

    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("Failed to create OR-Tools solver.")

    pipe_binary = {(i, j): solver.BoolVar(f"pipe[{i},{j}]") for i, j in edges}
    flow = {
        (i, j): solver.NumVar(-solver.infinity(), solver.infinity(), f"flow[{i},{j}]")
        for i, j in edges
    }
    build_center = {
        cell: solver.BoolVar(f"build_ec[{cell}]")
        for cell in town.energy_center_cells
    }

    big_m = total_demand
    for i, j in edges:
        solver.Add(flow[(i, j)] <= big_m * pipe_binary[(i, j)])
        solver.Add(flow[(i, j)] >= -big_m * pipe_binary[(i, j)])

    for cell in town.cells:
        net_flow_terms = []
        for neighbor in neighbors_by_cell[cell]:
            edge = (cell, neighbor) if cell < neighbor else (neighbor, cell)
            direction = -1 if cell == edge[0] else 1
            net_flow_terms.append(direction * flow[edge])
        net_flow = solver.Sum(net_flow_terms) if net_flow_terms else 0.0
        demand = cell_demands.get(cell, 0.0)
        generated = total_demand * build_center.get(cell, 0.0)
        solver.Add(net_flow + generated - demand >= 0)

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
    solver.Minimize(solver.Sum(objective_terms))

    status = solver.Solve()
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
