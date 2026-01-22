from math import sqrt
from typing import Any, Sequence
from dataclasses import dataclass

from ortools.sat.python import cp_model

from constants import DEMAND, HEAT_NETWORK_CONNECTION_COST_BUILDING
from layout import TownLayout

@dataclass
class SolverParameters():
    time_limit_seconds: int = 30
    relative_gap_limit: float = 0.01
    log_search_progress: bool = True


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


def _calculate_connection_cost(town: TownLayout) -> int:
    housing_multipliers = {"H20": 20, "H30": 30, "H40": 40}
    total_cost = 0
    for building in town.buildings:
        building_type = building["type"].name
        if building_type not in DEMAND:
            continue
        multiplier = housing_multipliers.get(building_type, 1)
        total_cost += multiplier * HEAT_NETWORK_CONNECTION_COST_BUILDING
    return total_cost


def _pipe_edge_cost(
    i: tuple[int, int],
    j: tuple[int, int],
    *,
    road_cells: set[tuple[int, int]],
    cost_pipe: int,
    cost_pipe_road: int,
) -> tuple[int, int, bool]:
    is_road = i in road_cells and j in road_cells
    edge_cost = cost_pipe_road if is_road else cost_pipe
    if abs(i[0] - j[0]) == 1 and abs(i[1] - j[1]) == 1:
        length_multiplier = sqrt(2)
    else:
        length_multiplier = 1.0
    length_cost = int(round(edge_cost * length_multiplier))
    length_meters = int(100.0 * length_multiplier)
    return length_cost, length_meters, is_road


def build_cell_demand_summary(town: TownLayout) -> list[dict[str, Any]]:
    cell_set = set(town.cells)
    road_cells = town.road_adjacent_cells
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
) -> dict[tuple[int, int], int]:
    cell_summaries = build_cell_demand_summary(town)
    cell_demands: dict[tuple[int, int], int] = {}
    for summary in cell_summaries:
        cell = summary["cell"]
        cell_demands[cell] = 1 if summary["demand"] > 0 else 0
    return cell_demands


def build_and_solve_model(
    town: TownLayout,
    *,
    cost_energy_center: int,
    cost_pipe: int,
    cost_pipe_road: int,
    solver_params: SolverParameters,
    time_limit_seconds: int | None = None,
    cell_demands: dict[tuple[int, int], int] | None = None,
    energy_center_cells: list[tuple[int, int]] | None = None,
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
            "costs": {
                "energy_centers": 0,
                "pipes_total": 0,
                "pipes_road": 0,
                "pipes_offroad": 0,
                "pipe_length_total_m": 0,
                "pipe_length_road_m": 0,
                "pipe_length_offroad_m": 0,
                "connections": 0,
                "total": 0,
            },
        }

    if energy_center_cells is None:
        energy_center_cells = town.energy_center_cells
    if not energy_center_cells:
        return {
            "status": "no-energy-centers",
            "objective_value": None,
            "energy_edges": [],
            "pipe_binary": {},
            "energy_centers": [],
            "costs": None,
        }

    # Calculate edges between neighboring cells (including diagonals)
    neighbor_deltas = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
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

    model = cp_model.CpModel()

    # Calculate which cells are adjacent to roads - these have a lower pipe cost
    road_cells = town.road_adjacent_cells

    # Decision variables
    pipe_binary = {(i, j): model.NewBoolVar(f"pipe[{i},{j}]") for i, j in edges}
    flow = {
        (i, j): model.NewIntVar(-total_demand, total_demand, f"flow[{i},{j}]")
        for i, j in edges
    }

    # Constraints
    for i, j in edges:
        model.Add(flow[(i, j)] <= total_demand * pipe_binary[(i, j)])
        model.Add(flow[(i, j)] >= -total_demand * pipe_binary[(i, j)])

    energy_center_set = set(energy_center_cells)
    for cell in town.cells:
        net_flow_terms = []
        for neighbor in neighbors_by_cell[cell]:
            edge = (cell, neighbor) if cell < neighbor else (neighbor, cell)
            direction = -1 if cell == edge[0] else 1
            net_flow_terms.append(direction * flow[edge])
        net_flow = sum(net_flow_terms) if net_flow_terms else 0
        demand = cell_demands.get(cell, 0)
        generated = total_demand if cell in energy_center_set else 0
        # generated = total_demand if build_center.get(cell, 0.0) else 0
        # print(f"Cell {cell}: net_flow + generated >= demand --> {net_flow} + {generated} >= {demand}")
        model.Add(net_flow + generated - demand >= 0)

    # Objective function
    objective_terms = []
    for (i, j), var in pipe_binary.items():
        length_cost, _, _ = _pipe_edge_cost(
            i,
            j,
            road_cells=road_cells,
            cost_pipe=cost_pipe,
            cost_pipe_road=cost_pipe_road,
        )
        objective_terms.append(var * length_cost)
    energy_center_cost = cost_energy_center * len(energy_center_cells)
    if energy_center_cost:
        objective_terms.append(energy_center_cost)
    connection_cost = _calculate_connection_cost(town)
    if connection_cost:
        objective_terms.append(connection_cost)
    model.Minimize(sum(objective_terms))

    # Solver parameters
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_params.time_limit_seconds
    solver.parameters.relative_gap_limit = solver_params.relative_gap_limit
    solver.parameters.log_search_progress = solver_params.log_search_progress

    # Solve
    status = solver.Solve(model)

    # Extract results
    pipe_binary_values = {edge: solver.Value(pipe_binary[edge]) for edge in pipe_binary}
    energy_edges = []
    for (i, j), value in pipe_binary_values.items():
        if value <= 0:
            continue
        energy_edges.append((i[0] + 0.5, i[1] + 0.5, j[0] + 0.5, j[1] + 0.5))
    energy_centers = list(energy_center_cells)
    pipe_costs = {"road": 0, "offroad": 0}
    pipe_lengths = {"road": 0, "offroad": 0}
    for (i, j), value in pipe_binary_values.items():
        if value <= 0:
            continue
        length_cost, length_meters, is_road = _pipe_edge_cost(
            i,
            j,
            road_cells=road_cells,
            cost_pipe=cost_pipe,
            cost_pipe_road=cost_pipe_road,
        )
        if is_road:
            pipe_costs["road"] += length_cost
            pipe_lengths["road"] += length_meters
        else:
            pipe_costs["offroad"] += length_cost
            pipe_lengths["offroad"] += length_meters
    total_cost = (
        energy_center_cost
        + connection_cost
        + pipe_costs["road"]
        + pipe_costs["offroad"]
    )

    return {
        "status": solver.StatusName(status),
        "objective_value": solver.ObjectiveValue()
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        else None,
        "energy_edges": energy_edges,
        "pipe_binary": pipe_binary_values,
        "energy_centers": energy_centers,
        "costs": {
            "energy_centers": energy_center_cost,
            "pipes_total": pipe_costs["road"] + pipe_costs["offroad"],
            "pipes_road": pipe_costs["road"],
            "pipes_offroad": pipe_costs["offroad"],
            "pipe_length_total_m": pipe_lengths["road"] + pipe_lengths["offroad"],
            "pipe_length_road_m": pipe_lengths["road"],
            "pipe_length_offroad_m": pipe_lengths["offroad"],
            "connections": connection_cost,
            "total": total_cost,
        }
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        else None,
    }
