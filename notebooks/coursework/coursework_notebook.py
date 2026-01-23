import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    from textwrap import dedent

    import marimo as mo
    import plotly.graph_objects as go

    import constants
    from layout import load_layout, CellType
    from model import build_and_solve_model, build_cell_demand_summary, SolverParameters
    from visualisation import build_town_plot
    return (
        CellType,
        Path,
        SolverParameters,
        build_and_solve_model,
        build_cell_demand_summary,
        build_town_plot,
        constants,
        dedent,
        go,
        load_layout,
        mo,
    )


@app.cell
def _(mo):
    layout_selector = mo.ui.dropdown(
        options={
            "Tiny test": "town_layout_tiny.json",
            "Small test": "town_layout_small.json",
            "Medium test": "town_layout_medium.json",
            "Full town": "town_layout_full.json",
        },
        value="Full town",
        label="Layout file",
    )
    mo.vstack([mo.md("### Layout"), layout_selector])
    return (layout_selector,)


@app.cell
def _(Path, layout_selector, load_layout):
    layout_path = (
        Path("notebooks")
        / "coursework"
        / "data"
        / layout_selector.value
    )
    town = load_layout(layout_path)
    return (town,)


@app.cell
def _(constants, dedent, mo, town):
    energy_center_md = "\t".join(
        [f"{{({x}, {y})}}" for x, y in town.energy_center_cells]
    )
    energy_center_checkboxes = {
        f"({x}, {y})": mo.ui.checkbox(
            value=False,
            label=f"({x}, {y})",
        )
        for x, y in town.energy_center_cells
    }
    param_form = (
        mo.md(
            dedent("""
                ### Model parameters

                Energy centre build cost (£): {cost_energy_center}

                Pipe cost per unit length (£): {cost_pipe}

                Pipe cost per unit length along roads (£): {cost_pipe_road}

                ### Solver parameters

                Time limit (seconds): {time_limit_seconds}
                Relative gap limit: {relative_gap_limit}

                ---

                Energy centres:

            """)
            + energy_center_md
        )
        .batch(
            cost_energy_center=mo.ui.number(value=constants.HEAT_NETWORK_ENERGY_CENTER_COST, step=1_000_000),
            cost_pipe=mo.ui.number(value=constants.HEAT_NETWORK_PIPE_COST_METER, step=10_000),
            cost_pipe_road=mo.ui.number(value=constants.HEAT_NETWORK_PIPE_COST_METER_ROAD, step=10_000),
            time_limit_seconds=mo.ui.number(value=30, step=5),
            relative_gap_limit=mo.ui.number(value=0.05, step=0.01),
            **energy_center_checkboxes,
        )
        .form(submit_button_label="Run optimisation", label="Parameters")
    )
    param_form
    return (param_form,)


@app.cell
def _(build_cell_demand_summary, mo, town):
    # Update demand summary if necessary
    cell_demand_summary = build_cell_demand_summary(town)
    demand_rows = [
        {
            "Building": summary["id"],
            "Type": summary["type"],
            "Representative cell": f"{summary['cell']}",
            "Winter demand (kWh)": round(summary["demand"], 2),
        }
        for summary in cell_demand_summary
    ]
    demand_table = mo.ui.table(demand_rows)
    return (demand_table,)


@app.cell
def _(SolverParameters, build_and_solve_model, param_form, town):
    submitted = param_form.value
    if submitted is None:
        optimisation_result = {
            "status": "Not run",
            "objective_value": None,
            "energy_edges": [],
            "pipe_binary": {},
            "energy_centers": [],
            "costs": None,
        }
    else:
        energy_center_cells = [
            (x, y)
            for x, y in town.energy_center_cells
            if submitted.get(f"({x}, {y})", False)
        ]
        solver_params = SolverParameters(
            time_limit_seconds=int(submitted["time_limit_seconds"]),
            relative_gap_limit=float(submitted["relative_gap_limit"]),
        )
        optimisation_result = build_and_solve_model(
            town,
            cost_energy_center=int(submitted["cost_energy_center"]),
            cost_pipe=int(submitted["cost_pipe"]),
            cost_pipe_road=int(submitted["cost_pipe_road"]),
            solver_params=solver_params,
            energy_center_cells=list(energy_center_cells),
        )
    return (optimisation_result,)


@app.cell
def _(mo, optimisation_result):
    _status = optimisation_result["status"]
    objective = optimisation_result["objective_value"]
    costs = optimisation_result.get("costs")
    if costs:
        breakdown_md = (
            f"**Cost breakdown:**  \n"
            f"- Energy centres: £{costs['energy_centers']:,.0f}  \n"
            f"- Pipes:  \n"
            f"  - Pipes (along roads): £{costs['pipes_road']:,.0f} (from {costs['pipe_length_road_m']:,.0f}m)  \n"
            f"  - Pipes (away from roads): £{costs['pipes_offroad']:,.0f} (from {costs['pipe_length_offroad_m']:,.0f}m)  \n"
            f"  - Pipes (total): £{costs['pipes_road'] + costs['pipes_offroad']:,.0f} (from {costs['pipe_length_total_m']:,.0f}m)  \n"
            f"- Connection costs: £{costs['connections']:,.0f}  \n"
            f"- **Total cost:** £{costs['total']:,.0f}  \n"
        )
    else:
        breakdown_md = ""
    status_md = mo.md(
        f"**Solver status:** {_status}  \n"
        f"**Objective value:** {objective}  \n"
        + breakdown_md
    )
    return (status_md,)


@app.cell
def _(mo):
    show_buildings = mo.ui.checkbox(value=True, label="Buildings")
    show_roads = mo.ui.checkbox(value=True, label="Roads")
    show_energy = mo.ui.checkbox(value=True, label="Energy network")

    controls = mo.hstack(
        [show_buildings, show_roads, show_energy],
        justify="start",
        align="center",
        gap=1,
    )
    mo.vstack(
        [
            mo.md("### Layers"),
            controls
        ]
    )
    return show_buildings, show_energy, show_roads


@app.cell
def _(
    build_town_plot,
    go,
    mo,
    optimisation_result,
    show_buildings,
    show_energy,
    show_roads,
    town,
):
    town_layout = town.buildings
    road_edges = town.road_edges
    building_metadata, center_lookup, icon_map, plot = build_town_plot(
        town_layout=town_layout,
        road_edges=road_edges,
        optimisation_result=optimisation_result,
        show_buildings=show_buildings,
        show_roads=show_roads,
        show_energy=show_energy,
        go=go,
        mo=mo,
    )
    return building_metadata, center_lookup, icon_map, plot


@app.cell
def _(mo):
    cell_type_colors = [
        ("low density housing", "rgb(255, 178, 220)"),
        ("medium density housing", "rgb(255, 0, 255)"),
        ("high density housing", "rgb(220, 25, 25)"),
        ("hospital", "rgb(0, 204, 255)"),
        ("shopping centre", "rgb(255, 204, 0)"),
        ("school", "rgb(160, 70, 20)"),
        ("office", "rgb(255, 255, 0)"),
        ("green space", "rgb(20, 163, 58)"),
        ("open space", "rgb(210, 210, 210)"),
        ("potential energy centre location", "rgb(60, 60, 60)"),
    ]

    def _swatch(color: str, shape: str = "square") -> str:
        if shape == "line":
            style = (
                "display:inline-block; width:24px; height:4px; "
                f"background:{color}; border:1px solid #333; "
                "vertical-align:middle; margin-right:6px;"
            )
        else:
            style = (
                "display:inline-block; width:14px; height:14px; "
                f"background:{color}; border:1px solid #333; "
                "vertical-align:middle; margin-right:6px;"
            )
            if shape == "dot":
                style += " border-radius:50%;"
        return f"<span style=\"{style}\"></span>"

    rows = []
    for label, color in cell_type_colors:
        rows.append(f"<div>{_swatch(color)}{label}</div>")
    energy_center_key = (
        "<span style=\"display:inline-block; width:16px; height:16px; "
        "background:rgb(224, 224, 0); border:1px solid #333; "
        "border-radius:50%; position:relative; vertical-align:middle; "
        "margin-right:6px;\">"
        "<span style=\"position:absolute; top:2px; left:2px; width:10px; "
        "height:10px; background:rgb(192, 0, 0); border-radius:50%;\"></span>"
        "</span>"
    )
    pipes_key = (
        "<span style=\"display:inline-block; width:24px; height:6px; "
        "background:rgb(224, 224, 0); border:1px solid #333; "
        "vertical-align:middle; margin-right:6px; position:relative;\">"
        "<span style=\"position:absolute; left:0; right:0; top:2px; "
        "height:2px; background:rgb(192, 0, 0);\"></span>"
        "</span>"
    )
    rows.append(f"<div>{energy_center_key}energy centre</div>")
    rows.append(f"<div>{pipes_key}pipes</div>")
    rows.append(f"<div>{_swatch('rgb(0, 0, 0)', 'line')}roads</div>")

    key_panel = mo.vstack(
        [
            mo.md("### Key"),
            mo.md("".join(rows)),
        ],
        align="start",
        gap=0,
    )
    return (key_panel,)


@app.cell
def _(
    CellType,
    Path,
    building_metadata,
    center_lookup,
    constants,
    icon_map,
    key_panel,
    mo,
    plot,
):
    selected = None
    value = plot.value
    points = []
    if isinstance(value, dict):
        points = value.get("points") or []
    elif value:
        points = value

    selected_point = None
    if points:
        for point in points:
            if isinstance(point, dict) and "cell_index" in point:
                selected_point = point
                break
        if selected_point is None:
            selected_point = points[0]

    if isinstance(selected_point, dict):
        cell_index = selected_point.get("cell_index")
        try:
            cell_index = int(cell_index)
        except (TypeError, ValueError):
            cell_index = None
        if isinstance(cell_index, int) and cell_index < len(building_metadata):
            selected = building_metadata[cell_index]
        elif "x" in selected_point and "y" in selected_point:
            key = (round(float(selected_point["x"]), 4), round(float(selected_point["y"]), 4))
            match_index = center_lookup.get(key)
            if match_index is not None:
                selected = building_metadata[match_index]

    if selected is not None:
        demand_by_label = {
            CellType[key].value: demand
            for key, demand in constants.DEMAND.items()
            if key in CellType.__members__
        }
        demand = demand_by_label.get(selected["type"])
        if demand:
            winter_thermal = demand.thermal_demand_kwh_year * demand.thermal_winter_factor
            mid_thermal = demand.thermal_demand_kwh_year * demand.thermal_mid_factor
            summer_thermal = demand.thermal_demand_kwh_year * demand.thermal_summer_factor
        else:
            winter_thermal = 0
            mid_thermal = 0
            summer_thermal = 0
        icon_file = icon_map.get(selected["type"])
        if icon_file:
            icon_path = Path("notebooks") / "coursework" / "img" / icon_file
            icon_view = mo.image(icon_path, alt=selected["type"], width=96)
        else:
            icon_view = mo.md("")
        info_panel = mo.vstack(
            [
                mo.md("### Cell details"),
                icon_view,
                mo.md(f"**Type:** {selected['type']}"),
                mo.md(
                    "**Coordinates:** "
                    f"({selected['x_min']}, {selected['y_min']}) -> "
                    f"({selected['x_max']}, {selected['y_max']})"
                ),
                mo.md(f"**Winter thermal demand:** {winter_thermal:,.0f}kWh"),
                mo.md(f"**Mid thermal demand:** {mid_thermal:,.0f}kWh"),
                mo.md(f"**Summer thermal demand:** {summer_thermal:,.0f}kWh"),
            ],
            align="center",
        )
    else:
        info_panel = mo.vstack(
            [
                mo.md("### Cell details"),
                mo.md("Click a cell to see its details."),
            ],
            align="center",
        )

    plot_with_key = mo.vstack([plot, key_panel], align="start", gap=0.5)
    layout = mo.hstack(
        [plot_with_key, info_panel],
        justify="start",
        align="start",
        widths=[3, 1],
        gap=1,
    )

    layout
    return


@app.cell
def _(mo, status_md):
    mo.vstack([mo.md("**Optimisation summary**"), status_md])
    return


@app.cell
def _(demand_table, mo):
    mo.vstack([mo.md("**Winter building demand**"), demand_table])
    return


@app.cell
def _(mo, optimisation_result):
    mo.vstack(
        [
            mo.md("**Optimisation Result**"),
            optimisation_result
        ]
    )
    return


if __name__ == "__main__":
    app.run()
