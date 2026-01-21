from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from pathlib import Path
import json

from gamspy import Container, Equation, Model, Parameter, Sense, Set, Sum, Variable


@dataclass(frozen=True)
class CellData:
    x_coord: float
    y_coord: float
    supply: float = 0.0
    population: float = 0.0
    ship_accessible: bool = False


@dataclass(frozen=True)
class GasNetworkData:
    cells: dict[str, CellData]
    demand_per_person: float = 2.0
    cost_pipe: float = 1_000_000.0
    max_flow: float = 22_000_000.0

def load_data_from_json(path: Path) -> GasNetworkData:
    """Load gas network data from JSON.

    Expected JSON structure:
    {
      "cells": {
        "c1": {
          "x_coord": 0.0,
          "y_coord": 0.0,
          "supply": 100.0,
          "population": 50.0,
          "ship_accessible": true
        },
        ...
      },
      "demand_per_person": 2.0,
      "cost_pipe": 1000000.0,
      "max_flow": 22000000.0
    }
    """
    raw = json.loads(path.read_text())
    cells = {
        name: CellData(
            x_coord=values["x_coord"],
            y_coord=values["y_coord"],
            supply=float(values.get("supply", 0.0)),
            population=float(values.get("population", 0.0)),
            ship_accessible=bool(values.get("ship_accessible", False)),
        )
        for name, values in raw["cells"].items()
    }
    return GasNetworkData(
        cells=cells,
        demand_per_person=float(raw.get("demand_per_person", 2.0)),
        cost_pipe=float(raw.get("cost_pipe", 1_000_000.0)),
        max_flow=float(raw.get("max_flow", 22_000_000.0)),
    )


def build_and_solve_model(data: GasNetworkData) -> dict:
    def _variable_to_dict(variable: Variable) -> dict[tuple[str, ...] | str, float]:
        if hasattr(variable, "to_dict"):
            data_dict = variable.to_dict()
            if isinstance(data_dict, dict):
                return data_dict
        records = variable.records
        if records is None:
            return {}
        index_columns = [
            column
            for column in records.columns
            if column not in {"level", "marginal", "lower", "upper", "scale"}
        ]
        values: dict[tuple[str, ...] | str, float] = {}
        for _, row in records.iterrows():
            key = tuple(row[column] for column in index_columns)
            if len(key) == 1:
                key = key[0]
            values[key] = float(row["level"])
        return values

    model_container = Container()

    # Sets
    cells = list(data.cells)
    pairs = [(i, j) for i in cells for j in cells if i != j]
    cells_set = Set(model_container, "cells", records=cells)
    pairs_set = Set(model_container, "pairs", domain=[cells_set, cells_set], records=pairs)

    # Variables
    pipe_binary = Variable(model_container, "pipe", domain=[pairs_set], type="Binary")
    flow = Variable(model_container, "flow", domain=[pairs_set], type="Positive")

    # Parameters
    distance = Parameter(
        model_container,
        "distance",
        domain=[pairs_set],
        records=[
            (
                i,
                j,
                hypot(
                    data.cells[i].x_coord - data.cells[j].x_coord,
                    data.cells[i].y_coord - data.cells[j].y_coord,
                ),
            )
            for i, j in pairs
        ],
    )
    supply = Parameter(
        model_container,
        "supply",
        domain=[cells_set],
        records=[(i, data.cells[i].supply) for i in cells],
    )
    demand = Parameter(
        model_container,
        "demand",
        domain=[cells_set],
        records=[
            (i, data.cells[i].population * data.demand_per_person) for i in cells
        ],
    )
    max_flow = Parameter(model_container, "max_flow", records=data.max_flow)
    cost_pipe = Parameter(model_container, "cost_pipe", records=data.cost_pipe)
    incidence = Parameter(
        model_container,
        "incidence",
        domain=[cells_set, pairs_set],
        records=[
            (cell, i, j, 1.0 if cell == j else -1.0)
            for i, j in pairs
            for cell in (i, j)
        ],
    )

    # Constraints
    flow_limit = Equation(model_container, "flow_limit", domain=[pairs_set])
    balance = Equation(model_container, "balance", domain=[cells_set])

    flow_limit[pairs_set] = flow[pairs_set] <= max_flow * pipe_binary[pairs_set]
    balance[cells_set] = (
        Sum(pairs_set, incidence[cells_set, pairs_set] * flow[pairs_set])
        + supply[cells_set]
        - demand[cells_set]
        >= 0
    )

    objective = Sum(pairs_set, pipe_binary[pairs_set] * cost_pipe * distance[pairs_set])
    model = Model(
        model_container,
        "gas_network",
        equations=[flow_limit, balance],
        sense=Sense.MIN,
        objective=objective,
        problem="MIP",
    )
    model.solve(solver="CPLEX")

    pipe_binary_values = _variable_to_dict(pipe_binary)
    flow_values = _variable_to_dict(flow)
    result = {
        "status": model.status,
        "objective_value": model.objective_value,
        "pipe_binary": pipe_binary_values,
        "flow": flow_values,
    }
    return result
