import marimo

__generated_with = "0.18.4"
app = marimo.App()


@app.cell
def _():
    import json
    from dataclasses import dataclass
    from math import hypot
    from pathlib import Path
    from typing import Sequence

    import marimo as mo
    from ortools.linear_solver import pywraplp

    return Path, Sequence, dataclass, hypot, json, mo, pywraplp


@app.cell
def _(Path, Sequence, dataclass, json):
    @dataclass(frozen=True)
    class GasNetworkData:
        cells: Sequence[str]
        ship_accessible_cells: Sequence[str]
        x_coord: dict[str, float]
        y_coord: dict[str, float]
        supply: dict[str, float]
        population: dict[str, float]
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

    return GasNetworkData, load_data_from_json


@app.cell
def _(GasNetworkData, hypot, pywraplp):
    def build_model(
        data: GasNetworkData,
    ) -> tuple[
        pywraplp.Solver,
        dict[tuple[str, str], pywraplp.Variable],
        dict[tuple[str, str], pywraplp.Variable],
    ]:
        solver = pywraplp.Solver.CreateSolver("SCIP")
        if solver is None:
            raise RuntimeError("Failed to create OR-Tools solver.")

        cells = list(data.cells)
        pairs = [(i, j) for i in cells for j in cells if i != j]

        pipe_binary = {(i, j): solver.BoolVar(f"pipe[{i},{j}]") for i, j in pairs}
        flow = {
            (i, j): solver.NumVar(0.0, solver.infinity(), f"flow[{i},{j}]")
            for i, j in pairs
        }

        objective_terms = []
        for i, j in pairs:
            distance = hypot(
                data.x_coord[i] - data.x_coord[j],
                data.y_coord[i] - data.y_coord[j],
            )
            objective_terms.append(pipe_binary[(i, j)] * data.cost_pipe * distance)
        solver.Minimize(solver.Sum(objective_terms))

        for i, j in pairs:
            solver.Add(flow[(i, j)] <= data.max_flow * pipe_binary[(i, j)])

        for i in cells:
            inflow = solver.Sum(flow[(j, i)] for j in cells if j != i)
            outflow = solver.Sum(flow[(i, j)] for j in cells if j != i)
            supply = data.supply.get(i, 0.0)
            demand = data.population.get(i, 0.0) * data.demand_per_person
            solver.Add(inflow - outflow + supply - demand >= 0)

        return solver, pipe_binary, flow

    return build_model


@app.cell
def _(build_model, pywraplp):
    def solve_model(data):
        solver, pipe_binary, flow = build_model(data)
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

    return solve_model


@app.cell
def _():
    def build_solution_table(pipe_binary, flow):
        rows = []
        for (i, j), value in pipe_binary.items():
            rows.append(
                {
                    "variable": "pipe_binary",
                    "from": i,
                    "to": j,
                    "value": value,
                }
            )
        for (i, j), value in flow.items():
            rows.append({"variable": "flow", "from": i, "to": j, "value": value})
        return rows

    return build_solution_table


@app.cell
def _(Path, build_solution_table, load_data_from_json, mo, solve_model):
    data = load_data_from_json(Path("files/base_case.json"))
    result = solve_model(data)
    table_rows = build_solution_table(result["pipe_binary"], result["flow"])

    status_md = mo.md(
        f"**Solver status:** {result['status']}  \n"
        f"**Objective value:** {result['objective_value']}"
    )
    solution_table = mo.ui.table(table_rows)

    mo.vstack([status_md, solution_table])
    return data, result, solution_table, status_md, table_rows


if __name__ == "__main__":
    app.run()
