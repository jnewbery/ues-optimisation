from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from pathlib import Path
import json

from ortools.linear_solver import pywraplp


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
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("Failed to create OR-Tools solver.")

    # Sets
    cells = list(data.cells)
    pairs = [(i, j) for i in cells for j in cells if i != j]

    # Variables
    pipe_binary = {(i, j): solver.BoolVar(f"pipe[{i},{j}]") for i, j in pairs}
    flow = {
        (i, j): solver.NumVar(0.0, solver.infinity(), f"flow[{i},{j}]")
        for i, j in pairs
    }

    # Objective
    objective_terms = []
    for i, j in pairs:
        distance = hypot(
            data.cells[i].x_coord - data.cells[j].x_coord,
            data.cells[i].y_coord - data.cells[j].y_coord,
        )
        objective_terms.append(pipe_binary[(i, j)] * data.cost_pipe * distance)
    solver.Minimize(solver.Sum(objective_terms))

    # Constraints
    for i, j in pairs:
        solver.Add(flow[(i, j)] <= data.max_flow * pipe_binary[(i, j)])
    for i in cells:
        inflow = solver.Sum(flow[(j, i)] for j in cells if j != i)
        outflow = solver.Sum(flow[(i, j)] for j in cells if j != i)
        supply = data.cells[i].supply
        demand = data.cells[i].population * data.demand_per_person
        solver.Add(inflow - outflow + supply - demand >= 0)

    status = solver.Solve()
    pipe_binary_values = {
        (i, j): var.solution_value() for (i, j), var in pipe_binary.items()
    }
    flow_values = {(i, j): var.solution_value() for (i, j), var in flow.items()}
    result = {
        "status": status,
        "objective_value": solver.Objective().Value()
        if status == pywraplp.Solver.OPTIMAL
        else None,
        "pipe_binary": pipe_binary_values,
        "flow": flow_values,
    }
    return result
