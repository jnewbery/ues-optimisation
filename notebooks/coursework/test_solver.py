from pathlib import Path

from layout import load_layout
from model import build_and_solve_model

layout_path = (
    Path("data")
    / "town_layout_tiny.json"
)
town = load_layout(layout_path)

optimisation_result = build_and_solve_model(
    town,
    cost_energy_center=2_000_000.0,
    cost_pipe=100_000.0,
)

breakpoint()
