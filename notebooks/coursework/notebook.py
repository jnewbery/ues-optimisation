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

    town_layout = []
    for y_index, row in enumerate(grid_layout):
        for x_index, cell in enumerate(row):
            town_layout.append(
                {
                    "x_min": x_index,
                    "x_max": x_index + 1,
                    "y_min": y_index,
                    "y_max": y_index + 1,
                    "type": CellType[cell]
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


if __name__ == "__main__":
    app.run()
