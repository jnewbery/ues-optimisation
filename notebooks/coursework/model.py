import math
from typing import Any, Sequence

from gamspy import Container, Equation, Model, Parameter, Sense, Set, Sum, Variable

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

    def _variable_to_dict(variable: Variable) -> dict[Any, float]:
        if hasattr(variable, "to_dict"):
            data = variable.to_dict()
            if isinstance(data, dict):
                return data
        records = variable.records
        if records is None:
            return {}
        index_columns = [
            column
            for column in records.columns
            if column not in {"level", "marginal", "lower", "upper", "scale"}
        ]
        values: dict[Any, float] = {}
        for _, row in records.iterrows():
            key = tuple(row[column] for column in index_columns)
            if len(key) == 1:
                key = key[0]
            values[key] = float(row["level"])
        return values

    cell_ids = {cell: f"c{idx}" for idx, cell in enumerate(town.cells)}
    id_to_cell = {cell_id: cell for cell, cell_id in cell_ids.items()}
    edge_records = [(cell_ids[i], cell_ids[j]) for i, j in edges]
    energy_cell_ids = [cell_ids[cell] for cell in town.energy_center_cells]

    model_container = Container()
    cells_set = Set(model_container, "cells", records=list(cell_ids.values()))
    edges_set = Set(model_container, "edges", domain=[cells_set, cells_set], records=edge_records)
    demand = Parameter(
        model_container,
        "demand",
        domain=[cells_set],
        records=[(cell_ids[cell], value) for cell, value in cell_demands.items()],
    )
    edge_length = Parameter(
        model_container,
        "edge_length",
        domain=[edges_set],
        records=[
            (
                cell_ids[i],
                cell_ids[j],
                math.sqrt((i[0] - j[0]) ** 2 + (i[1] - j[1]) ** 2),
            )
            for i, j in edges
        ],
    )
    incidence = Parameter(
        model_container,
        "incidence",
        domain=[cells_set, edges_set],
        records=[
            (
                cell_ids[cell],
                cell_ids[i],
                cell_ids[j],
                -1.0 if cell == i else 1.0,
            )
            for i, j in edges
            for cell in (i, j)
        ],
    )
    energy_indicator = Parameter(
        model_container,
        "energy_indicator",
        domain=[cells_set],
        records=[(cell_id, 1.0) for cell_id in energy_cell_ids],
    )
    big_m = Parameter(model_container, "big_m", records=total_demand)
    pipe_cost = Parameter(model_container, "pipe_cost", records=cost_pipe)
    center_cost = Parameter(model_container, "center_cost", records=cost_energy_center)

    pipe_binary = Variable(model_container, "pipe", domain=[edges_set], type="Binary")
    flow = Variable(model_container, "flow", domain=[edges_set], type="Free")
    build_center = Variable(model_container, "build_center", domain=[cells_set], type="Binary")
    build_center.up[cells_set] = energy_indicator[cells_set]

    flow_upper = Equation(model_container, "flow_upper", domain=[edges_set])
    flow_lower = Equation(model_container, "flow_lower", domain=[edges_set])
    balance = Equation(model_container, "balance", domain=[cells_set])

    flow_upper[edges_set] = flow[edges_set] <= big_m * pipe_binary[edges_set]
    flow_lower[edges_set] = flow[edges_set] >= -big_m * pipe_binary[edges_set]
    balance[cells_set] = (
        Sum(edges_set, incidence[cells_set, edges_set] * flow[edges_set])
        + total_demand * build_center[cells_set]
        - demand[cells_set]
        >= 0
    )

    objective = Sum(edges_set, pipe_binary[edges_set] * pipe_cost * edge_length[edges_set]) + Sum(
        cells_set, build_center[cells_set] * center_cost
    )
    model = Model(
        model_container,
        "energy_network",
        equations=[flow_upper, flow_lower, balance],
        sense=Sense.MIN,
        objective=objective,
        problem="MIP",
    )
    model.solve(solver="CPLEX")

    pipe_binary_values_raw = _variable_to_dict(pipe_binary)
    pipe_binary_values = {
        (id_to_cell[i], id_to_cell[j]): value
        for (i, j), value in pipe_binary_values_raw.items()
    }
    energy_edges = []
    for (i, j), value in pipe_binary_values.items():
        if value <= 0.5:
            continue
        energy_edges.append((i[0] + 0.5, i[1] + 0.5, j[0] + 0.5, j[1] + 0.5))
    energy_centers = []
    build_center_values = _variable_to_dict(build_center)
    for cell_id, value in build_center_values.items():
        if value > 0.5:
            energy_centers.append(id_to_cell[cell_id])

    return {
        "status": model.status,
        "objective_value": model.objective_value,
        "energy_edges": energy_edges,
        "pipe_binary": pipe_binary_values,
        "energy_centers": energy_centers,
    }
