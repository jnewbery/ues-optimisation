"""OR-Tools translation of the AIMMS Main_GasSupplyNetwork model.

The AIMMS model is defined in files/gas_supply_network.txt. The data in
files/BaseCase.data is a binary AIMMS case file, which this script does not
attempt to parse. Instead, provide a JSON input with the structure described
in load_data_from_json().
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import hypot
from pathlib import Path
from typing import Dict, Iterable, Sequence

from ortools.linear_solver import pywraplp


@dataclass(frozen=True)
class GasNetworkData:
    cells: Sequence[str]
    ship_accessible_cells: Sequence[str]
    x_coord: Dict[str, float]
    y_coord: Dict[str, float]
    supply: Dict[str, float]
    population: Dict[str, float]
    demand_per_person: float = 2.0
    cost_pipe: float = 1_000_000.0
    max_flow: float = 22_000_000.0


def load_data_from_json(path: Path) -> GasNetworkData:
    """Load gas network data from JSON.

    Expected JSON structure:
    {
      "cells": ["c1", "c2", ...],
      "ship_accessible_cells": ["c1", ...],
      "x_coord": {"c1": 0.0, "c2": 1.2, ...},
      "y_coord": {"c1": 0.0, "c2": 2.1, ...},
      "supply": {"c1": 100.0, ...},
      "population": {"c1": 50.0, ...},
      "demand_per_person": 2.0,
      "cost_pipe": 1000000.0,
      "max_flow": 22000000.0
    }
    """
    raw = json.loads(path.read_text())
    return GasNetworkData(
        cells=raw["cells"],
        ship_accessible_cells=raw.get("ship_accessible_cells", []),
        x_coord=raw["x_coord"],
        y_coord=raw["y_coord"],
        supply=raw.get("supply", {}),
        population=raw.get("population", {}),
        demand_per_person=float(raw.get("demand_per_person", 2.0)),
        cost_pipe=float(raw.get("cost_pipe", 1_000_000.0)),
        max_flow=float(raw.get("max_flow", 22_000_000.0)),
    )


def build_model(data: GasNetworkData) -> tuple[pywraplp.Solver, dict[tuple[str, str], pywraplp.Variable], dict[tuple[str, str], pywraplp.Variable]]:
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("Failed to create OR-Tools solver.")

    cells = list(data.cells)
    pairs = [(i, j) for i in cells for j in cells if i != j]

    pipe_binary = {
        (i, j): solver.BoolVar(f"pipe[{i},{j}]") for i, j in pairs
    }
    flow = {
        (i, j): solver.NumVar(0.0, solver.infinity(), f"flow[{i},{j}]") for i, j in pairs
    }

    # Objective: minimize capital cost
    objective_terms = []
    for i, j in pairs:
        distance = hypot(data.x_coord[i] - data.x_coord[j], data.y_coord[i] - data.y_coord[j])
        objective_terms.append(pipe_binary[(i, j)] * data.cost_pipe * distance)
    solver.Minimize(solver.Sum(objective_terms))

    # Flow only when pipe exists
    for i, j in pairs:
        solver.Add(flow[(i, j)] <= data.max_flow * pipe_binary[(i, j)])

    # Material balance
    for i in cells:
        inflow = solver.Sum(flow[(j, i)] for j in cells if j != i)
        outflow = solver.Sum(flow[(i, j)] for j in cells if j != i)
        supply = data.supply.get(i, 0.0)
        demand = data.population.get(i, 0.0) * data.demand_per_person
        solver.Add(inflow - outflow + supply - demand >= 0)

    return solver, pipe_binary, flow


def solve_model(data: GasNetworkData) -> dict[str, object]:
    solver, pipe_binary, flow = build_model(data)
    status = solver.Solve()
    result = {
        "status": status,
        "objective_value": solver.Objective().Value() if status == pywraplp.Solver.OPTIMAL else None,
        "pipe_binary": {f"{i},{j}": var.solution_value() for (i, j), var in pipe_binary.items()},
        "flow": {f"{i},{j}": var.solution_value() for (i, j), var in flow.items()},
    }
    return result


def main(argv: Iterable[str]) -> int:
    args = list(argv)
    if len(args) < 2:
        raise SystemExit("Usage: python gas_supply_network_ortools.py <data.json>")
    data_path = Path(args[1])
    data = load_data_from_json(data_path)
    result = solve_model(data)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv))
