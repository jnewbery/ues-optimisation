import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path
    from dataclasses import dataclass
    import enum

    from town_rendering import render_town_layout
    return Path, dataclass, enum, mo, render_town_layout


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
    ENERGY_CENTRE_CAPEX = 5_000_000 * 100  # £5m per energy centre

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

    type_map = {
        "20": "low density housing",
        "30": "medium density housing",
        "40": "high density housing",
        "EC": "potential energy centre",
        "H": "hospital",
        "SC": "shopping centre",
        "SCH": "school",
        "OF": "office",
        "O": "open space",
        "G": "green space",
    }

    mid_heat_demand_map = {
        "20": 20,
        "30": 30,
        "40": 40,
    }

    summer_heat_demand_map = {
        "20": 20,
        "30": 30,
        "40": 40,
    }

    def resolve_cell_type(cell: str) -> CellType:
        if cell == "SH":
            return CellType.SC
        return CellType[cell]

    merge_types = {"H", "OF", "SCH", "SC"}
    town_layout = []
    visited = set()
    max_y = len(grid_layout)

    for y_index, row in enumerate(grid_layout):
        for x_index, cell in enumerate(row):
            if cell in merge_types:
                if (x_index, y_index) in visited:
                    continue

                stack = [(x_index, y_index)]
                visited.add((x_index, y_index))
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
                        if not (0 <= y_next < max_y):
                            continue
                        if not (0 <= x_next < len(grid_layout[y_next])):
                            continue
                        if (x_next, y_next) in visited:
                            continue
                        if grid_layout[y_next][x_next] != cell:
                            continue
                        visited.add((x_next, y_next))
                        stack.append((x_next, y_next))

                x_min = min(x for x, _ in component)
                x_max = max(x for x, _ in component) + 1
                y_min = min(y for _, y in component)
                y_max = max(y for _, y in component) + 1
                town_layout.append(
                    {
                        "x_min": x_min,
                        "x_max": x_max,
                        "y_min": y_min,
                        "y_max": y_max,
                        "building_type": resolve_cell_type(cell),
                    }
                )
            else:
                town_layout.append(
                    {
                        "x_min": x_index,
                        "x_max": x_index + 1,
                        "y_min": y_index,
                        "y_max": y_index + 1,
                        "building_type": resolve_cell_type(cell),
                    }
                )
    return (town_layout,)


@app.cell
def _(Path, mo, render_town_layout, town_layout):
    image_dir = Path("notebooks") / "coursework" / "img"
    town_image = render_town_layout(town_layout, image_dir)
    mo.vstack(
        [
            mo.md("## Coursework town layout"),
            mo.image(town_image, alt="Coursework town layout"),
        ]
    )
    return


@app.cell
def _(CellType, DEMAND, dataclass, town_layout):
    @dataclass(frozen=True)
    class HeatNode:
        name: str
        x_coord: float
        y_coord: float
        building_type: CellType
        winter_heat_demand_kwh: float
        is_energy_centre: bool

    def winter_thermal_demand(building_type: CellType, area: int) -> float:
        demand_data = DEMAND.get(building_type)
        if demand_data is None:
            return 0.0
        return (
            demand_data.thermal_demand_kwh_year
            * demand_data.thermal_winter_factor
            * area
        )

    nodes = []
    for index, building in enumerate(town_layout, start=1):
        x_min = building["x_min"]
        x_max = building["x_max"]
        y_min = building["y_min"]
        y_max = building["y_max"]
        area = (x_max - x_min) * (y_max - y_min)
        building_type = building["building_type"]
        nodes.append(
            HeatNode(
                name=f"b{index}",
                x_coord=(x_min + x_max) / 2,
                y_coord=(y_min + y_max) / 2,
                building_type=building_type,
                winter_heat_demand_kwh=winter_thermal_demand(building_type, area),
                is_energy_centre=building_type == CellType.EC,
            )
        )

    total_winter_heat_demand = sum(node.winter_heat_demand_kwh for node in nodes)
    return HeatNode, nodes, total_winter_heat_demand, winter_thermal_demand


@app.cell
def _(HeatNode, total_winter_heat_demand):
    from math import hypot
    from ortools.linear_solver import pywraplp

    def build_and_solve_heat_network(
        nodes: list[HeatNode],
        cost_energy_centre: float,
        cost_pipe: float,
    ) -> dict:
        solver = pywraplp.Solver.CreateSolver("SCIP")
        if solver is None:
            raise RuntimeError("Failed to create OR-Tools solver.")

        node_names = [node.name for node in nodes]
        node_lookup = {node.name: node for node in nodes}
        pairs = [(i, j) for i in node_names for j in node_names if i != j]

        pipe_binary = {(i, j): solver.BoolVar(f"pipe[{i},{j}]") for i, j in pairs}
        flow = {
            (i, j): solver.NumVar(0.0, solver.infinity(), f"flow[{i},{j}]")
            for i, j in pairs
        }
        build_centre = {
            node.name: solver.BoolVar(f"build[{node.name}]")
            for node in nodes
            if node.is_energy_centre
        }
        heat_generated = {
            node.name: solver.NumVar(0.0, solver.infinity(), f"heat[{node.name}]")
            for node in nodes
        }

        objective_terms = []
        for i, j in pairs:
            distance = hypot(
                node_lookup[i].x_coord - node_lookup[j].x_coord,
                node_lookup[i].y_coord - node_lookup[j].y_coord,
            )
            objective_terms.append(pipe_binary[(i, j)] * cost_pipe * distance)
        for node in nodes:
            if node.is_energy_centre:
                objective_terms.append(build_centre[node.name] * cost_energy_centre)
        solver.Minimize(solver.Sum(objective_terms))

        max_flow = total_winter_heat_demand
        for i, j in pairs:
            solver.Add(flow[(i, j)] <= max_flow * pipe_binary[(i, j)])

        for node in nodes:
            if node.is_energy_centre:
                solver.Add(
                    heat_generated[node.name]
                    <= total_winter_heat_demand * build_centre[node.name]
                )
            else:
                solver.Add(heat_generated[node.name] == 0.0)

        for node in nodes:
            inflow = solver.Sum(
                flow[(j, node.name)] for j in node_names if j != node.name
            )
            outflow = solver.Sum(
                flow[(node.name, j)] for j in node_names if j != node.name
            )
            solver.Add(
                inflow
                + heat_generated[node.name]
                - outflow
                - node.winter_heat_demand_kwh
                >= 0
            )

        status = solver.Solve()
        pipe_binary_values = {
            (i, j): var.solution_value() for (i, j), var in pipe_binary.items()
        }
        flow_values = {(i, j): var.solution_value() for (i, j), var in flow.items()}
        heat_values = {name: var.solution_value() for name, var in heat_generated.items()}
        build_values = {
            name: var.solution_value() for name, var in build_centre.items()
        }
        result = {
            "status": status,
            "objective_value": solver.Objective().Value()
            if status == pywraplp.Solver.OPTIMAL
            else None,
            "pipe_binary": pipe_binary_values,
            "flow": flow_values,
            "heat_generated": heat_values,
            "build_centre": build_values,
        }
        return result

    return (build_and_solve_heat_network,)


@app.cell
def _(ENERGY_CENTRE_CAPEX, HEAT_NETWORK_PIPE_COST_METER, mo):
    demand_form = (
        mo.md(
            """
            **Heat network optimisation parameters**

            Energy centre build cost: {energy_centre_cost}

            Pipe installation cost (per meter): {pipe_cost}
            """
        )
        .batch(
            energy_centre_cost=mo.ui.number(
                value=ENERGY_CENTRE_CAPEX,
                step=100_000.0,
            ),
            pipe_cost=mo.ui.number(
                value=HEAT_NETWORK_PIPE_COST_METER,
                step=100_000.0,
            ),
        )
        .form(submit_button_label="Run optimisation", label="Model Parameters")
    )
    demand_form
    return (demand_form,)


@app.cell
def _(ENERGY_CENTRE_CAPEX, HEAT_NETWORK_PIPE_COST_METER, demand_form):
    submitted = demand_form.value
    if submitted is None:
        cost_energy_centre = ENERGY_CENTRE_CAPEX
        cost_pipe = HEAT_NETWORK_PIPE_COST_METER
    else:
        cost_energy_centre = submitted["energy_centre_cost"]
        cost_pipe = submitted["pipe_cost"]
    return cost_energy_centre, cost_pipe


@app.cell
def _(build_and_solve_heat_network, cost_energy_centre, cost_pipe, nodes):
    heat_network_result = build_and_solve_heat_network(
        nodes,
        cost_energy_centre=cost_energy_centre,
        cost_pipe=cost_pipe,
    )
    return (heat_network_result,)


@app.cell
def _(mo, nodes, total_winter_heat_demand):
    demand_rows = [
        {
            "Building": node.name,
            "Type": node.building_type.value,
            "Winter demand (kWh)": node.winter_heat_demand_kwh,
            "Energy centre site": node.is_energy_centre,
        }
        for node in nodes
    ]
    mo.vstack(
        [
            mo.md(f"**Total winter heat demand:** {total_winter_heat_demand:,.0f} kWh"),
            mo.md("**Building winter heat demands**"),
            mo.ui.table(demand_rows),
        ]
    )
    return (demand_rows,)


@app.cell
def _(mo, nodes, heat_network_result):
    from math import hypot

    node_lookup = {node.name: node for node in nodes}
    built_centres = []
    for node in nodes:
        if not node.is_energy_centre:
            continue
        built_centres.append(
            {
                "Energy centre": node.name,
                "Built": heat_network_result["build_centre"].get(node.name, 0.0),
                "Heat generated (kWh)": heat_network_result["heat_generated"].get(
                    node.name, 0.0
                ),
            }
        )

    pipe_rows = []
    for (i, j), built in heat_network_result["pipe_binary"].items():
        if built < 0.5:
            continue
        distance = hypot(
            node_lookup[i].x_coord - node_lookup[j].x_coord,
            node_lookup[i].y_coord - node_lookup[j].y_coord,
        )
        pipe_rows.append(
            {
                "From": i,
                "To": j,
                "Distance (cells)": distance,
                "Flow (kWh)": heat_network_result["flow"][(i, j)],
            }
        )

    status_md = mo.md(
        f"**Solver status:** {heat_network_result['status']}  \n"
        f"**Objective value:** {heat_network_result['objective_value']}"
    )
    mo.vstack(
        [
            mo.md("## Heat network optimisation results"),
            status_md,
            mo.md("**Energy centre build decisions**"),
            mo.ui.table(built_centres),
            mo.md("**Installed pipes**"),
            mo.ui.table(pipe_rows),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
