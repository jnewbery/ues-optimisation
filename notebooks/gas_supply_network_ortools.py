import marimo

__generated_with = "0.18.4"
app = marimo.App()


@app.cell
def _():
    import json
    from dataclasses import dataclass, replace
    from math import hypot
    from pathlib import Path
    from typing import Sequence

    import marimo as mo
    from ortools.linear_solver import pywraplp

    return Path, Sequence, dataclass, hypot, json, mo, pywraplp, replace


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
    def build_solution_grid(cells, values, fill_value=0.0):
        rows = []
        for i in cells:
            row = {"from": i}
            for j in cells:
                row[j] = values.get((i, j), fill_value)
            rows.append(row)
        return rows

    return build_solution_grid


@app.cell
def _(Path, load_data_from_json):
    base_data = load_data_from_json(Path("files/base_case.json"))
    return base_data


@app.cell
def _(base_data, mo):
    param_form = (
        mo.md(
            """
            **Update parameters**

            Demand per person: {demand_per_person}

            Pipe cost: {cost_pipe}

            Max flow: {max_flow}
            """
        )
        .batch(
            demand_per_person=mo.ui.number(
                value=base_data.demand_per_person, step=0.1
            ),
            cost_pipe=mo.ui.number(value=base_data.cost_pipe, step=100_000.0),
            max_flow=mo.ui.number(value=base_data.max_flow, step=100_000.0),
        )
        .form(submit_button_label="Run optimisation", label="Parameters")
    )
    param_form
    return param_form


@app.cell
def _(base_data, param_form, replace):
    submitted_params = param_form.value
    if submitted_params is None:
        params = {
            "demand_per_person": base_data.demand_per_person,
            "cost_pipe": base_data.cost_pipe,
            "max_flow": base_data.max_flow,
        }
    else:
        params = submitted_params
    data = replace(base_data, **params)
    return data, params


@app.cell
def _(build_solution_grid, data, mo, solve_model):
    result = solve_model(data)
    pipe_binary_grid = build_solution_grid(data.cells, result["pipe_binary"])
    flow_grid = build_solution_grid(data.cells, result["flow"])

    status_md = mo.md(
        f"**Solver status:** {result['status']}  \n"
        f"**Objective value:** {result['objective_value']}"
    )
    pipe_binary_table = mo.ui.table(pipe_binary_grid)
    flow_table = mo.ui.table(flow_grid)
    pipe_binary_md = mo.md("**Pipe binaries (14x14)**")
    flow_md = mo.md("**Flow (14x14)**")

    mo.vstack([status_md, pipe_binary_md, pipe_binary_table, flow_md, flow_table])
    return (
        result,
        pipe_binary_table,
        flow_table,
        pipe_binary_md,
        flow_md,
        status_md,
        pipe_binary_grid,
        flow_grid,
    )


if __name__ == "__main__":
    app.run()
