import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from dataclasses import dataclass
    import enum
    import json
    import math
    from pathlib import Path

    import marimo as mo
    from ortools.linear_solver import pywraplp
    import plotly.graph_objects as go
    return Path, dataclass, enum, go, json, math, mo, pywraplp


@app.cell
def _(enum):
    class CellType(enum.StrEnum):
        H20 = "low density housing"
        H30 = "medium density housing"
        H40 = "high density housing"
        EC = "potential energy centre"
        H = "hospital"
        SC = "shopping centre"
        SCH = "school"
        OF = "office"
        O = "open space"
        G = "green space"
    return (CellType,)


@app.cell
def _(CellType, dataclass):
    # Constants
    GAS_PRICE_DOMESTIC_P_KWH = 6
    GAS_PRICE_COMMERCIAL_P_KWH = 9
    ELECTRICITY_PRICE_DOMESTIC_P_KWH = 28
    ELECTRICITY_PRICE_COMMERCIAL_P_KWH = 30
    ELECTRICITY_EXPORT_DOMESTIC_P_KWH = 6
    ELECTRICITY_EXPORT_COMMERCIAL_P_KWH = 18
    HEAT_NETWORK_PIPE_COST_METER = 1000 * 100  # £1000 per meter
    HEAT_NETWORK_CONNECTION_COST_BUILDING = 1700 * 100  # £1700 per connection

    @dataclass
    class DemandData:
        electricity_demand_kwh_year: int
        electricity_summer_factor: float
        electricity_mid_factor: float
        electricity_winter_factor: float
        thermal_demand_kwh_year: int
        thermal_summer_factor: float
        thermal_mid_factor: float
        thermal_winter_factor: float

    _SINGLE_HOUSEHOLD_DEMAND = DemandData(
        electricity_demand_kwh_year=3200,
        electricity_summer_factor=0.8,
        electricity_mid_factor=1.0,
        electricity_winter_factor=1.2,
        thermal_demand_kwh_year=11200,
        thermal_summer_factor=0.5,
        thermal_mid_factor=1.0,
        thermal_winter_factor=1.5
    )

    DEMAND = {
        CellType.H20: DemandData(
            electricity_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.electricity_demand_kwh_year * 20,
            electricity_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_summer_factor,
            electricity_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_mid_factor,
            electricity_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_winter_factor,
            thermal_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.thermal_demand_kwh_year * 20,
            thermal_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_summer_factor,
            thermal_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_mid_factor,
            thermal_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_winter_factor
        ),
        CellType.H30: DemandData(
            electricity_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.electricity_demand_kwh_year * 30,
            electricity_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_summer_factor,
            electricity_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_mid_factor,
            electricity_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_winter_factor,
            thermal_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.thermal_demand_kwh_year * 30,
            thermal_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_summer_factor,
            thermal_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_mid_factor,
            thermal_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_winter_factor
        ),
        CellType.H40: DemandData(
            electricity_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.electricity_demand_kwh_year * 40,
            electricity_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_summer_factor,
            electricity_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_mid_factor,
            electricity_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_winter_factor,
            thermal_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.thermal_demand_kwh_year * 40,
            thermal_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_summer_factor,
            thermal_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_mid_factor,
            thermal_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_winter_factor
        ),
        CellType.SCH: DemandData(
            electricity_demand_kwh_year=147000,
            electricity_summer_factor=0.7,
            electricity_mid_factor=1.1,
            electricity_winter_factor=1.1,
            thermal_demand_kwh_year=617000,
            thermal_summer_factor=0.15,
            thermal_mid_factor=1.0,
            thermal_winter_factor=1.85,
        ),
        CellType.SC: DemandData(
            electricity_demand_kwh_year=14726250,
            electricity_summer_factor=1.3,
            electricity_mid_factor=1.0,
            electricity_winter_factor=0.7,
            thermal_demand_kwh_year=4908750,
            thermal_summer_factor=0.25,
            thermal_mid_factor=1.0,
            thermal_winter_factor=1.75,
        ),
        CellType.H: DemandData(
            electricity_demand_kwh_year=675000,
            electricity_summer_factor=1.3,
            electricity_mid_factor=1.0,
            electricity_winter_factor=0.7,
            thermal_demand_kwh_year=2250000,
            thermal_summer_factor=0.35,
            thermal_mid_factor=1.0,
            thermal_winter_factor=1.65,
        ),
        CellType.OF: DemandData(
            electricity_demand_kwh_year=2600000,
            electricity_summer_factor=0.8,
            electricity_mid_factor=1.0,
            electricity_winter_factor=1.2,
            thermal_demand_kwh_year=6200000,
            thermal_summer_factor=0.5,
            thermal_mid_factor=1.0,
            thermal_winter_factor=1.5,
        ),
    }
    return (DEMAND,)


@app.cell
def _(mo):
    layout_selector = mo.ui.dropdown(
        options={
            "Tiny test": "town_layout_tiny.json",
            "Small test": "town_layout_small.json",
            "Medium test": "town_layout_medium.json",
            "Full town": "town_layout.json",
        },
        value="Full town",
        label="Layout file",
    )
    mo.vstack([mo.md("### Layout"), layout_selector])
    return (layout_selector,)


@app.cell
def _(CellType, Path, json, layout_selector):
    layout_path = (
        Path("notebooks")
        / "coursework"
        / "data"
        / layout_selector.value
    )
    with layout_path.open() as handle:
        layout_data = json.load(handle)
    grid_layout = layout_data["grid_layout"]
    road_edges = [
        (tuple(edge[0]), tuple(edge[1]))
        for edge in layout_data["road_edges"]
    ]

    merge_types = {"H", "OF", "SCH", "SC"}
    town_layout = []
    visited = set()
    _max_y = len(grid_layout)

    for _y_index, _row in enumerate(grid_layout):
        for _x_index, _cell in enumerate(_row):
            if _cell in merge_types:
                if (_x_index, _y_index) in visited:
                    continue

                stack = [(_x_index, _y_index)]
                visited.add((_x_index, _y_index))
                component = []

                while stack:
                    _x_cell, _y_cell = stack.pop()
                    component.append((_x_cell, _y_cell))
                    neighbors = (
                        (_x_cell - 1, _y_cell),
                        (_x_cell + 1, _y_cell),
                        (_x_cell, _y_cell - 1),
                        (_x_cell, _y_cell + 1),
                    )
                    for x_next, y_next in neighbors:
                        if not (0 <= y_next < _max_y):
                            continue
                        if not (0 <= x_next < len(grid_layout[y_next])):
                            continue
                        if (x_next, y_next) in visited:
                            continue
                        if grid_layout[y_next][x_next] != _cell:
                            continue
                        visited.add((x_next, y_next))
                        stack.append((x_next, y_next))

                _x_min = min(x for x, _ in component)
                _x_max = max(x for x, _ in component) + 1
                _y_min = min(y for _, y in component)
                _y_max = max(y for _, y in component) + 1
                town_layout.append(
                    {
                        "x_min": _x_min,
                        "x_max": _x_max,
                        "y_min": _y_min,
                        "y_max": _y_max,
                        "type": CellType[_cell],
                    }
                )
            else:
                town_layout.append(
                    {
                        "x_min": _x_index,
                        "x_max": _x_index + 1,
                        "y_min": _y_index,
                        "y_max": _y_index + 1,
                        "type": CellType[_cell],
                    }
                )
    return grid_layout, road_edges, town_layout


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
def _(mo):
    show_buildings = mo.ui.checkbox(value=True, label="Buildings")
    show_roads = mo.ui.checkbox(value=True, label="Roads")
    show_energy = mo.ui.checkbox(value=False, label="Energy network")

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
def _(CellType, DEMAND, grid_layout, town_layout):
    cells = [
        (x_index, y_index)
        for y_index, _row in enumerate(grid_layout)
        for x_index, _ in enumerate(_row)
    ]
    _cell_set = set(cells)
    energy_center_cells = [
        (x_index, y_index)
        for y_index, _row in enumerate(grid_layout)
        for x_index, _cell in enumerate(_row)
        if _cell == CellType.EC.name
    ]
    building_demands = []
    for building_index, _building in enumerate(town_layout):
        _building_type = _building["type"]
        _demand = DEMAND.get(_building_type)
        if _demand is None:
            continue
        footprint = [
            (x_cell, y_cell)
            for x_cell in range(_building["x_min"], _building["x_max"])
            for y_cell in range(_building["y_min"], _building["y_max"])
            if (x_cell, y_cell) in _cell_set
        ]
        if not footprint:
            continue
        _winter_thermal = (
            _demand.thermal_demand_kwh_year * _demand.thermal_winter_factor
        )
        _total_demand = _winter_thermal * len(footprint)
        building_demands.append(
            {
                "id": building_index,
                "type": _building_type.value,
                "demand": _total_demand,
                "footprint": footprint,
            }
        )
    return building_demands, cells, energy_center_cells


@app.cell
def _(
    building_demands,
    cells,
    energy_center_cells,
    math,
    param_form,
    pywraplp,
):
    def build_and_solve_model(cost_energy_center, cost_pipe):
        _total_demand = sum(building["demand"] for building in building_demands)
        if _total_demand == 0:
            return {
                "status": "no-demand",
                "objective_value": 0.0,
                "energy_edges": [],
                "pipe_binary": {},
            }

        _cell_set = set(cells)
        neighbor_deltas = [
            (dx, dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if not (dx == 0 and dy == 0)
        ]
        edges = []
        neighbors_by_cell = {_cell: [] for _cell in cells}
        for _x_cell, _y_cell in cells:
            for dx, dy in neighbor_deltas:
                nx = _x_cell + dx
                ny = _y_cell + dy
                if (nx, ny) not in _cell_set:
                    continue
                neighbors_by_cell[(_x_cell, _y_cell)].append((nx, ny))
                if (_x_cell, _y_cell) < (nx, ny):
                    edges.append(((_x_cell, _y_cell), (nx, ny)))

        solver = pywraplp.Solver.CreateSolver("SCIP")
        if solver is None:
            raise RuntimeError("Failed to create OR-Tools solver.")

        pipe_binary = {
            (i, j): solver.BoolVar(f"pipe[{i},{j}]")
            for i, j in edges
        }
        flow = {}
        for i, j in edges:
            flow[(i, j)] = solver.NumVar(0.0, solver.infinity(), f"flow[{i},{j}]")
            flow[(j, i)] = solver.NumVar(0.0, solver.infinity(), f"flow[{j},{i}]")

        build_center = {
            _cell: solver.BoolVar(f"build_ec[{_cell}]")
            for _cell in energy_center_cells
        }
        assignment = {}
        for _building in building_demands:
            for _cell in _building["footprint"]:
                assignment[(_building["id"], _cell)] = solver.BoolVar(
                    f"assign[{_building['id']},{_cell}]"
                )

        for _building in building_demands:
            solver.Add(
                solver.Sum(
                    assignment[(_building["id"], _cell)]
                    for _cell in _building["footprint"]
                )
                == 1
            )

        big_m = _total_demand
        for i, j in edges:
            solver.Add(flow[(i, j)] <= big_m * pipe_binary[(i, j)])
            solver.Add(flow[(j, i)] <= big_m * pipe_binary[(i, j)])

        for _cell in cells:
            inflow = solver.Sum(
                flow[(neighbor, _cell)] for neighbor in neighbors_by_cell[_cell]
            )
            outflow = solver.Sum(
                flow[(_cell, neighbor)] for neighbor in neighbors_by_cell[_cell]
            )
            _demand = solver.Sum(
                _building["demand"] * assignment[(_building["id"], _cell)]
                for _building in building_demands
                if _cell in _building["footprint"]
            )
            generated = _total_demand * build_center.get(_cell, 0.0)
            solver.Add(inflow + generated - outflow - _demand >= 0)

        objective_terms = []
        for (i, j), var in pipe_binary.items():
            dx = i[0] - j[0]
            dy = i[1] - j[1]
            length = math.sqrt(dx * dx + dy * dy)
            objective_terms.append(var * cost_pipe * length)
        objective_terms.extend(
            build_center[_cell] * cost_energy_center
            for _cell in energy_center_cells
        )
        solver.Minimize(solver.Sum(objective_terms))

        _status = solver.Solve()
        pipe_binary_values = {
            edge: pipe_binary[edge].solution_value()
            for edge in pipe_binary
        }
        energy_edges = []
        for (i, j), _value in pipe_binary_values.items():
            if _value <= 0.5:
                continue
            energy_edges.append(
                (i[0] + 0.5, i[1] + 0.5, j[0] + 0.5, j[1] + 0.5)
            )

        return {
            "status": _status,
            "objective_value": solver.Objective().Value()
            if _status == pywraplp.Solver.OPTIMAL
            else None,
            "energy_edges": energy_edges,
            "pipe_binary": pipe_binary_values,
        }

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
            cost_energy_center=float(submitted["cost_energy_center"]),
            cost_pipe=float(submitted["cost_pipe"]),
        )
    return (optimisation_result,)


@app.cell
def _(building_demands, mo, optimisation_result):
    _status = optimisation_result["status"]
    objective = optimisation_result["objective_value"]
    status_md = mo.md(
        f"**Solver status:** {_status}  \n"
        f"**Objective value:** {objective}"
    )
    demand_rows = [
        {
            "Building": building["id"],
            "Type": building["type"],
            "Winter demand (kWh)": round(building["demand"], 2),
        }
        for building in building_demands
    ]
    demand_table = mo.ui.table(demand_rows)
    return demand_table, status_md


@app.cell
def _(
    go,
    mo,
    optimisation_result,
    road_edges,
    show_buildings,
    show_energy,
    show_roads,
    town_layout,
):
    icon_map = {
        "low density housing": "housing-low-density.png",
        "medium density housing": "housing-med-density.png",
        "high density housing": "housing-high-density.png",
        "potential energy centre": "energy-centre.png",
        "hospital": "hospital.png",
        "shopping centre": "shopping-centre.png",
        "school": "school.png",
        "office": "office.png",
        "green space": "green-space.png",
        "open space": "open-space.png",
    }
    color_map = {
        "low density housing": "rgb(255, 178, 220)",
        "medium density housing": "rgb(255, 0, 255)",
        "high density housing": "rgb(220, 25, 25)",
        "green space": "rgb(20, 163, 58)",
        "potential energy centre": "rgb(60, 60, 60)",
        "open space": "rgb(210, 210, 210)",
        "hospital": "rgb(0, 204, 255)",
        "shopping centre": "rgb(255, 204, 0)",
        "school": "rgb(160, 70, 20)",
        "office": "rgb(255, 255, 0)",
    }
    cell_size = 48

    max_x = max(building["x_max"] for building in town_layout)
    max_y = max(building["y_max"] for building in town_layout)

    building_traces = []
    building_metadata = []
    center_lookup = {}
    marker_x = []
    marker_y = []
    marker_sizes = []
    marker_customdata = []

    for idx, building in enumerate(town_layout):
        building_type = building["type"].value
        x0 = building["x_min"]
        x1 = building["x_max"]
        y0 = building["y_min"]
        y1 = building["y_max"]
        building_metadata.append(
            {
                "type": building_type,
                "x_min": x0,
                "x_max": x1,
                "y_min": y0,
                "y_max": y1,
            }
        )
        width = x1 - x0
        height = y1 - y0
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        marker_x.append(center_x)
        marker_y.append(center_y)
        marker_customdata.append(idx)
        center_lookup[(round(center_x, 4), round(center_y, 4))] = idx
        marker_sizes.append(max(width, height) * cell_size * 0.8)
        fill_color = color_map.get(building_type, "rgb(180, 180, 180)")
        building_traces.append(
            go.Scatter(
                x=[x0, x1, x1, x0, x0],
                y=[y0, y0, y1, y1, y0],
                fill="toself",
                mode="lines",
                line={"color": "rgb(90, 90, 90)", "width":1},
                fillcolor=fill_color.replace("rgb", "rgba").replace(")", ", 0.8)"),
                hoverinfo="skip",
                name="Buildings",
                legendgroup="buildings",
                showlegend=idx == 0,
            )
        )

    road_traces = []
    for idx, ((x0, y0), (x1, y1)) in enumerate(road_edges):
        road_traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"color": "rgb(0, 0, 0)", "width": 4},
                hoverinfo="skip",
                name="Roads",
                legendgroup="roads",
                showlegend=idx == 0,
            )
        )
    if not road_traces:
        road_traces.append(
            go.Scatter(
                x=[],
                y=[],
                mode="lines",
                line={"color": "rgb(0, 0, 0)", "width": 2},
                hoverinfo="skip",
                name="Roads",
                legendgroup="roads",
                showlegend=True,
            )
        )

    energy_network_edges = optimisation_result.get("energy_edges", [])
    energy_traces = []
    for idx, (x0, y0, x1, y1) in enumerate(energy_network_edges):
        energy_traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"color": "rgb(20, 20, 20)", "width": 3},
                hoverinfo="skip",
                name="Energy network",
                legendgroup="energy",
                showlegend=idx == 0,
            )
        )
    if not energy_traces:
        energy_traces.append(
            go.Scatter(
                x=[],
                y=[],
                mode="lines",
                line={"color": "rgb(20, 20, 20)", "width": 3},
                hoverinfo="skip",
                name="Energy network",
                legendgroup="energy",
                showlegend=True,
            )
        )

    building_interaction_trace = go.Scatter(
        x=marker_x,
        y=marker_y,
        mode="markers",
        marker={"size": marker_sizes, "opacity": 0.01},
        customdata=marker_customdata,
        hovertemplate="cell_index=%{customdata}<extra></extra>",
        name="Building interactions",
        showlegend=False,
    )

    fig = go.Figure()
    if show_buildings.value:
        fig.add_traces(building_traces)
        fig.add_trace(building_interaction_trace)
    if show_roads.value:
        fig.add_traces(road_traces)
    if show_energy.value:
        fig.add_traces(energy_traces)

    fig.update_layout(
        title="Town layout",
        clickmode="event+select",
        xaxis={
            "visible": False,
            "range": [0, max_x],
            "constrain": "domain",
        },
        yaxis={
            "visible": False,
            "range": [max_y, 0],
            "scaleanchor": "x",
        },
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        width=int(max_x * cell_size + 80),
        height=int(max_y * cell_size + 80),
        legend={"orientation": "h"},
    )
    plot = mo.ui.plotly(fig)
    return building_metadata, center_lookup, icon_map, plot


@app.cell
def _(DEMAND, Path, building_metadata, center_lookup, icon_map, mo, plot):
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
        demand_by_label = {cell_type.value: demand for cell_type, demand in DEMAND.items()}
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
def _(demand_table, mo, status_md):
    mo.vstack([status_md, mo.md("**Winter building demand**"), demand_table])
    return


@app.cell
def _(mo, optimisation_result):
    mo.vstack(
        [
            mo.md("##Optimisation Result"),
            optimisation_result
        ]
    )
    return


if __name__ == "__main__":
    app.run()
