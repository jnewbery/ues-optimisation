from dataclasses import dataclass


GAS_PRICE_DOMESTIC_P_KWH = 6
GAS_PRICE_COMMERCIAL_P_KWH = 9
ELECTRICITY_PRICE_DOMESTIC_P_KWH = 28
ELECTRICITY_PRICE_COMMERCIAL_P_KWH = 30
ELECTRICITY_EXPORT_DOMESTIC_P_KWH = 6
ELECTRICITY_EXPORT_COMMERCIAL_P_KWH = 18
HEAT_NETWORK_PIPE_COST_METER = 1000 * 100  # £1000 per meter
HEAT_NETWORK_PIPE_COST_METER_ROAD = HEAT_NETWORK_PIPE_COST_METER // 2  # 50% less to build pipe under road
HEAT_NETWORK_CONNECTION_COST_BUILDING = 1700  # £1700 per connection
HEAT_NETWORK_ENERGY_CENTER_COST = 18_000_000  # £18,000,000 per energy centre


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
    thermal_winter_factor=1.5,
)

DEMAND = {
    "H20": DemandData(
        electricity_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.electricity_demand_kwh_year
        * 20,
        electricity_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_summer_factor,
        electricity_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_mid_factor,
        electricity_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_winter_factor,
        thermal_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.thermal_demand_kwh_year * 20,
        thermal_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_summer_factor,
        thermal_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_mid_factor,
        thermal_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_winter_factor,
    ),
    "H30": DemandData(
        electricity_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.electricity_demand_kwh_year
        * 30,
        electricity_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_summer_factor,
        electricity_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_mid_factor,
        electricity_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_winter_factor,
        thermal_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.thermal_demand_kwh_year * 30,
        thermal_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_summer_factor,
        thermal_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_mid_factor,
        thermal_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_winter_factor,
    ),
    "H40": DemandData(
        electricity_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.electricity_demand_kwh_year
        * 40,
        electricity_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_summer_factor,
        electricity_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_mid_factor,
        electricity_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.electricity_winter_factor,
        thermal_demand_kwh_year=_SINGLE_HOUSEHOLD_DEMAND.thermal_demand_kwh_year * 40,
        thermal_summer_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_summer_factor,
        thermal_mid_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_mid_factor,
        thermal_winter_factor=_SINGLE_HOUSEHOLD_DEMAND.thermal_winter_factor,
    ),
    "SCH": DemandData(
        electricity_demand_kwh_year=147000,
        electricity_summer_factor=0.7,
        electricity_mid_factor=1.1,
        electricity_winter_factor=1.1,
        thermal_demand_kwh_year=617000,
        thermal_summer_factor=0.15,
        thermal_mid_factor=1.0,
        thermal_winter_factor=1.85,
    ),
    "SC": DemandData(
        electricity_demand_kwh_year=14726250,
        electricity_summer_factor=1.3,
        electricity_mid_factor=1.0,
        electricity_winter_factor=0.7,
        thermal_demand_kwh_year=4908750,
        thermal_summer_factor=0.25,
        thermal_mid_factor=1.0,
        thermal_winter_factor=1.75,
    ),
    "H": DemandData(
        electricity_demand_kwh_year=675000,
        electricity_summer_factor=1.3,
        electricity_mid_factor=1.0,
        electricity_winter_factor=0.7,
        thermal_demand_kwh_year=2250000,
        thermal_summer_factor=0.35,
        thermal_mid_factor=1.0,
        thermal_winter_factor=1.65,
    ),
    "OF": DemandData(
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
