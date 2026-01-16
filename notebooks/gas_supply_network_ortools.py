import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell
def _():
    from pathlib import Path
    from dataclasses import replace

    import marimo as mo

    from src.gas_network_model import (
        CellData,
        GasNetworkData,
        build_and_solve_model,
        load_data_from_json,
    )
    from src.gas_network_rendering import (
        build_solution_grid,
        render_network_diagram,
    )
    return (
        CellData,
        GasNetworkData,
        Path,
        build_and_solve_model,
        build_solution_grid,
        load_data_from_json,
        mo,
        render_network_diagram,
        replace,
    )


@app.cell
def _(Path, load_data_from_json):
    base_data = load_data_from_json(Path("files/base_case.json"))
    return (base_data,)


@app.cell
def _(base_data, mo):
    supply_cell_names = sorted(
        base_data.cells,
        key=lambda name: int(name.removeprefix("c")),
    )
    default_supply_cells = {
        name
        for name, cell in base_data.cells.items()
        if cell.supply > 0
    }
    if not default_supply_cells:
        default_supply_cells = {
            name
            for name, cell in base_data.cells.items()
            if cell.ship_accessible
        }
    supply_checkboxes = {
        f"supply_{name}": mo.ui.checkbox(
            value=name in default_supply_cells,
            label=f"Cell {name.removeprefix('c')}",
            disabled=not base_data.cells[name].ship_accessible,
        )
        for name in supply_cell_names
    }
    supply_controls = mo.vstack(
        [supply_checkboxes[f"supply_{name}"] for name in supply_cell_names],
        gap=0.25,
    )
    param_form = (
        mo.md(
            """
            Demand per person: {demand_per_person}

            Pipe cost: {cost_pipe}

            Max flow: {max_flow}

            LNG supply cells:

            {supply_cells}
            """
        )
        .batch(
            demand_per_person=mo.ui.number(
                value=base_data.demand_per_person, step=0.1
            ),
            cost_pipe=mo.ui.number(value=base_data.cost_pipe, step=100_000.0),
            max_flow=mo.ui.number(value=base_data.max_flow, step=100_000.0),
            supply_cells=supply_controls,
            **supply_checkboxes,
        )
        .form(submit_button_label="Run optimisation", label="Model Parameters")
    )
    param_form
    return (param_form,)


@app.cell
def _(base_data, param_form, replace):
    submitted_params = param_form.value
    if submitted_params is None:
        params = {
            "demand_per_person": base_data.demand_per_person,
            "cost_pipe": base_data.cost_pipe,
            "max_flow": base_data.max_flow,
        }
        supply_selection = {
            name: cell.supply > 0
            for name, cell in base_data.cells.items()
        }
    else:
        params = {
            "demand_per_person": submitted_params["demand_per_person"],
            "cost_pipe": submitted_params["cost_pipe"],
            "max_flow": submitted_params["max_flow"],
        }
        supply_selection = {
            name: submitted_params[f"supply_{name}"]
            for name in base_data.cells
        }
    supply_amount = max(cell.supply for cell in base_data.cells.values())
    updated_cells = {
        name: replace(
            cell,
            supply=supply_amount if supply_selection[name] else 0.0,
        )
        for name, cell in base_data.cells.items()
    }
    data = replace(base_data, cells=updated_cells, **params)
    return (data,)


@app.cell
def _(
    build_and_solve_model,
    build_solution_grid,
    data,
    mo,
    render_network_diagram,
):
    result = build_and_solve_model(data)

    status_md = mo.md(
        f"**Solver status:** {result['status']}  \n"
        f"**Objective value:** {result['objective_value']}"
    )

    diagram = render_network_diagram(data, result)
    diagram_view = mo.image(diagram, alt="Optimised gas network diagram")

    pipe_binary_md = mo.md("**Pipe binaries (14x14)**")
    pipe_binary_grid = build_solution_grid(data.cells, result["pipe_binary"])
    pipe_binary_table = mo.ui.table(pipe_binary_grid)

    flow_md = mo.md("**Flow (14x14)**")
    flow_grid = build_solution_grid(data.cells, result["flow"])
    flow_table = mo.ui.table(flow_grid)

    diagram_md = mo.md("**Optimised network diagram**")

    mo.vstack(
        [
            status_md,
            diagram_md,
            diagram_view,
            pipe_binary_md,
            pipe_binary_table,
            flow_md,
            flow_table,
        ]
    )
    return


if __name__ == "__main__":
    app.run()
