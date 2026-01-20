import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import plotly.graph_objects as go

    from constants import DEMAND
    from layout import load_layout, CellType
    from model import build_and_solve_model, build_building_demands
    from visualisation import build_town_plot
    return (
        CellType,
        DEMAND,
        Path,
        build_and_solve_model,
        build_building_demands,
        build_town_plot,
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
def _(mo):
    param_form = (
        mo.md(
            """
            Energy centre build cost (£): {cost_energy_center}

            Pipe cost per unit length (£): {cost_pipe}
            """
        )
        .batch(
            cost_energy_center=mo.ui.number(value=2_000_000.0, step=100_000.0),
            cost_pipe=mo.ui.number(value=100_000.0, step=10_000.0),
        )
        .form(submit_button_label="Run optimisation", label="Model Parameters")
    )
    param_form
    return (param_form,)


@app.cell
def _(build_building_demands, mo, town):
    # Update building demands if necessary
    building_demands = build_building_demands(town)
    demand_rows = [
        {
            "Building": building["id"],
            "Type": building["type"],
            "Winter demand (kWh)": round(building["demand"], 2),
        }
        for building in building_demands
    ]
    demand_table = mo.ui.table(demand_rows)
    return building_demands, demand_table


@app.cell
def _(build_and_solve_model, param_form, town):
    submitted = param_form.value
    if submitted is None:
        optimisation_result = {
            "status": "not-run",
            "objective_value": None,
            "energy_edges": [],
            "pipe_binary": {},
        }
    else:
        optimisation_result = build_and_solve_model(
            town,
            cost_energy_center=float(submitted["cost_energy_center"]),
            cost_pipe=float(submitted["cost_pipe"]),
        )
    return (optimisation_result,)


@app.cell
def _(mo, optimisation_result):
    _status = optimisation_result["status"]
    objective = optimisation_result["objective_value"]
    objective_str = f"£{round(objective, 2)}" if objective else "None"
    status_md = mo.md(
        f"**Solver status:** {_status}  \n"
        f"**Objective value:** {objective_str}"
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
def _(
    CellType,
    DEMAND,
    Path,
    building_metadata,
    center_lookup,
    icon_map,
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
            for key, demand in DEMAND.items()
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

    layout = mo.hstack(
        [plot, info_panel],
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
