import math
from typing import Any, Sequence

from ortools.linear_solver import pywraplp

from constants import DEMAND
from layout import TownLayout


def build_building_demands(
    town: TownLayout,
) -> list[dict[str, Any]]:
    cell_set = set(town.cells)
    building_demands = []
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
        building_demands.append(
            {
                "id": building_index,
                "type": building_type.value,
                "demand": total_demand,
                "footprint": footprint,
            }
        )
    return building_demands


def build_and_solve_model(
    town: TownLayout,
    *,
    cost_energy_center: float,
    cost_pipe: float,
    building_demands: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if building_demands is None:
        building_demands = build_building_demands(town)

    total_demand = sum(building["demand"] for building in building_demands)
    if total_demand == 0:
        return {
            "status": "no-demand",
            "objective_value": 0.0,
            "energy_edges": [],
            "pipe_binary": {},
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

    assignment = {}
    for building in building_demands:
        for cell in building["footprint"]:
            assignment[(building["id"], cell)] = solver.BoolVar(
                f"assign[{building['id']},{cell}]"
            )

    for building in building_demands:
        solver.Add(
            solver.Sum(
                assignment[(building["id"], cell)] for cell in building["footprint"]
            )
            == 1
        )

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
        demand = solver.Sum(
            building["demand"] * assignment[(building["id"], cell)]
            for building in building_demands
            if cell in building["footprint"]
        )
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

    return {
        "status": status,
        "objective_value": solver.Objective().Value()
        if status == pywraplp.Solver.OPTIMAL
        else None,
        "energy_edges": energy_edges,
        "pipe_binary": pipe_binary_values,
    }
