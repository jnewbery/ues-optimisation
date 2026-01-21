from decimal import Decimal
from typing import Any, Sequence

from ortools.sat.python import cp_model

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
    time_limit_seconds: int | None = None,
    cell_demands: dict[tuple[int, int], int] | None = None,
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
    neighbor_deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
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

    # Decision variables
    pipe_binary = {(i, j): model.NewBoolVar(f"pipe[{i},{j}]") for i, j in edges}
    flow = {
        (i, j): model.NewIntVar(-total_demand, total_demand, f"flow[{i},{j}]")
        for i, j in edges
    }
    # build_center = {
    #     cell: model.NewBoolVar(f"build_ec[{cell}]")
    #     for cell in town.energy_center_cells
    # }

    # Constraints
    for i, j in edges:
        model.Add(flow[(i, j)] <= total_demand * pipe_binary[(i, j)])
        model.Add(flow[(i, j)] >= -total_demand * pipe_binary[(i, j)])

    for cell in town.cells:
        net_flow_terms = []
        for neighbor in neighbors_by_cell[cell]:
            edge = (cell, neighbor) if cell < neighbor else (neighbor, cell)
            direction = -1 if cell == edge[0] else 1
            net_flow_terms.append(direction * flow[edge])
        net_flow = sum(net_flow_terms) if net_flow_terms else 0
        demand = cell_demands.get(cell, 0)
        generated = total_demand if cell == (0, 0) else 0
        # generated = total_demand if build_center.get(cell, 0.0) else 0
        # print(f"Cell {cell}: net_flow + generated >= demand --> {net_flow} + {generated} >= {demand}")
        model.Add(net_flow + generated - demand >= 0)

    # Objective function
    objective_terms = []
    for (i, j), var in pipe_binary.items():
        # length = math.sqrt(dx * dx + dy * dy)
        length = 1
        objective_terms.append(var * cost_pipe * length)
    # objective_terms.extend(
    #     build_center[cell] * cost_energy_center
    #     for cell in town.energy_center_cells
    # )

    # Solve
    model.Minimize(sum(objective_terms))
    solver = cp_model.CpSolver()
    if time_limit_seconds is not None:
        solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    status = solver.Solve(model)

    # Extract results
    pipe_binary_values = {edge: solver.Value(pipe_binary[edge]) for edge in pipe_binary}
    energy_edges = []
    for (i, j), value in pipe_binary_values.items():
        if value <= 0:
            continue
        energy_edges.append((i[0] + 0.5, i[1] + 0.5, j[0] + 0.5, j[1] + 0.5))
    energy_centers = []
    energy_centers.append((0, 0))
    # if status == pywraplp.Solver.OPTIMAL:
    #     for cell, var in build_center.items():
    #         if var.solution_value() > 0.5:
    #             energy_centers.append(cell)

    return {
        "status": solver.StatusName(status),
        "objective_value": solver.ObjectiveValue()
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        else None,
        "energy_edges": energy_edges,
        "pipe_binary": pipe_binary_values,
        "energy_centers": energy_centers,
    }
