import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    from dataclasses import dataclass
    import enum
    import base64

    import plotly.graph_objects as go
    return Path, base64, dataclass, enum, go, mo


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
    return


@app.cell
def _(CellType):
    grid_layout = [
        [ "H20", "H20", "H20", "H20", "H20", "H20",   "G", "H20", "H20",   "H",   "H",   "H"],
        [ "H20", "H30", "H30", "H30", "H30", "H30",   "G", "H20", "H20",   "H",   "H",   "H"],
        [ "H20", "H30",   "G",   "G", "H30", "H30",   "G",   "G",   "G",   "G",   "G", "H20"],
        [ "H20", "H30", "H30", "H30", "H30", "H30",   "G",   "G",   "G",   "G",   "G", "H20"],
        [ "H20", "H30", "H40", "H40", "H40", "H40", "H30", "H30", "H30", "H30",   "G", "H20"],
        [ "H20", "H30",   "G",   "G",  "SC",  "SC", "H30", "H30", "H30", "H30",   "G", "H20"],
        [ "H20", "H30",  "EC",   "O",  "SC",  "SC",   "O", "H30", "H30", "H30", "H30", "H20"],
        [ "H20",   "O",  "EC",   "O",  "SC",  "SC",   "O", "H20", "H20", "H20", "H20", "H20"],
        [ "H20",   "O",   "O",   "O",  "SC",  "SC",   "O",   "O",  "EC",  "EC",   "O", "H20"],
        [ "H20", "H20",   "O",   "O",  "OF",  "OF",   "O",   "O",   "O",   "O",   "O", "H20"],
        [ "H20", "H20", "H20", "H20",  "OF",  "OF",   "O", "SCH", "SCH",   "G",   "G", "H20"],
        [  "EC",  "EC", "H20", "H20", "H20", "H20",   "O", "SCH", "SCH",   "G",   "G", "H20"],
        [  "EC",  "EC", "H20", "H20", "H30", "H30", "H20", "H20",   "G",   "G",   "G", "H20"],
    ]


    def resolve_cell_type(cell: str) -> CellType:
        if cell == "SH":
            return CellType.SC
        return CellType[cell]

    merge_types = {"H", "OF", "SCH", "SC"}
    town_layout = []
    visited = set()
    _max_y = len(grid_layout)

    for _y_index, row in enumerate(grid_layout):
        for _x_index, cell in enumerate(row):
            if cell in merge_types:
                if (_x_index, _y_index) in visited:
                    continue

                stack = [(_x_index, _y_index)]
                visited.add((_x_index, _y_index))
                component = []

                while stack:
                    x_cell, y_cell = stack.pop()
                    component.append((x_cell, y_cell))
                    neighbors = (
                        (x_cell - 1, y_cell),
                        (x_cell + 1, y_cell),
                        (x_cell, y_cell - 1),
                        (x_cell, y_cell + 1),
                    )
                    for x_next, y_next in neighbors:
                        if not (0 <= y_next < _max_y):
                            continue
                        if not (0 <= x_next < len(grid_layout[y_next])):
                            continue
                        if (x_next, y_next) in visited:
                            continue
                        if grid_layout[y_next][x_next] != cell:
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
                        "type": CellType[cell],
                    }
                )
            else:
                town_layout.append(
                    {
                        "x_min": _x_index,
                        "x_max": _x_index + 1,
                        "y_min": _y_index,
                        "y_max": _y_index + 1,
                        "type": CellType[cell],
                    }
                )
    return (town_layout,)


@app.cell
def _(Path, base64, go, mo, town_layout):
    image_dir = Path("notebooks") / "coursework" / "img"

    def icon_data_uri(filename: str) -> str:
        icon_path = image_dir / filename
        if not icon_path.exists():
            return ""
        data = icon_path.read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    icon_map = {
        "low density housing": "housing-low-density.png",
        "medium density housing": "housing-med-density.png",
        "high density housing": "housing-high-density.png",
        "potential energy centre": "energy-centre.png",
        "hospital": "hospital.png",
        "shopping centre": "shopping_centre.png",
        "school": "school.png",
        "office": "office.png",
    }
    icon_uri_map = {
        label: icon_data_uri(filename) for label, filename in icon_map.items()
    }
    color_map = {
        "low density housing": "rgb(255, 178, 220)",
        "medium density housing": "rgb(255, 0, 255)",
        "high density housing": "rgb(220, 25, 25)",
        "green space": "rgb(196, 234, 214)",
        "potential energy centre": "rgb(20, 20, 20)",
        "open space": "rgb(210, 210, 210)",
        "hospital": "rgb(0, 204, 255)",
        "shopping centre": "rgb(255, 204, 0)",
        "school": "rgb(160, 70, 20)",
        "office": "rgb(255, 255, 0)",
    }

    show_buildings = mo.ui.checkbox(value=True, label="Buildings")
    show_rows = mo.ui.checkbox(value=True, label="Rows")
    show_energy = mo.ui.checkbox(value=False, label="Energy network (stub)")

    max_x = max(building["x_max"] for building in town_layout)
    max_y = max(building["y_max"] for building in town_layout)

    building_traces = []
    for idx, building in enumerate(town_layout):
        building_type = building["type"].value
        x0 = building["x_min"]
        x1 = building["x_max"]
        y0 = building["y_min"]
        y1 = building["y_max"]
        icon_uri = icon_uri_map.get(building_type, "")
        if icon_uri:
            hover = (
                f"<b>{building_type}</b><br>"
                f"<img src='{icon_uri}' width='64' height='64'>"
            )
        else:
            hover = f"<b>{building_type}</b>"
        fill_color = color_map.get(building_type, "rgb(180, 180, 180)")
        building_traces.append(
            go.Scatter(
                x=[x0, x1, x1, x0, x0],
                y=[y0, y0, y1, y1, y0],
                fill="toself",
                mode="lines",
                line={"color": "rgb(90, 90, 90)"},
                fillcolor=fill_color.replace("rgb", "rgba").replace(")", ", 0.8)"),
                hovertemplate=hover + "<extra></extra>",
                name="Buildings",
                legendgroup="buildings",
                showlegend=idx == 0,
            )
        )

    row_traces = []
    for y_index in range(max_y + 1):
        row_traces.append(
            go.Scatter(
                x=[0, max_x],
                y=[y_index, y_index],
                mode="lines",
                line={"color": "rgba(60, 60, 60, 0.25)", "width": 1},
                hoverinfo="skip",
                name="Rows",
                legendgroup="rows",
                showlegend=y_index == 0,
            )
        )

    energy_network_edges = []
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

    fig = go.Figure()
    if show_buildings.value:
        fig.add_traces(building_traces)
    if show_rows.value:
        fig.add_traces(row_traces)
    if show_energy.value:
        fig.add_traces(energy_traces)

    fig.update_layout(
        title="Coursework town layout",
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
        legend={"orientation": "h"},
    )

    controls = mo.hstack([show_buildings, show_rows, show_energy])
    mo.vstack(
        [
            mo.md("## Coursework town layout"),
            controls,
            mo.ui.plotly(fig),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
