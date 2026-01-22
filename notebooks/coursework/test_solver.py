from pathlib import Path

import constants
from layout import load_layout
from model import build_and_solve_model, SolverParameters
from argparse import ArgumentParser

LAYOUT_DIR = Path("data")

def _main(layout_path: Path, time_limit: int, gap_limit: float) -> None:
    town = load_layout(layout_path)

    solver_params = SolverParameters(
        time_limit_seconds=time_limit,
        relative_gap_limit=gap_limit,
    )

    optimisation_result = build_and_solve_model(
        town,
        cost_energy_center=constants.HEAT_NETWORK_ENERGY_CENTER_COST,
        cost_pipe=constants.HEAT_NETWORK_PIPE_COST_METER,
        cost_pipe_road=constants.HEAT_NETWORK_PIPE_COST_METER_ROAD,
        solver_params=solver_params,
    )

    print("Optimisation Result:")
    for key, value in optimisation_result.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    arg_parser = ArgumentParser(description="Run town energy optimisation.")
    layouts = [
        p.name for p in LAYOUT_DIR.glob("*.json")
    ]

    arg_parser.add_argument(
        "--layout",
        "-l",
        type=Path,
        default=Path("data") / "town_layout_tiny.json",
        help="Path to the town layout JSON file. Options: "+ ", ".join(layouts),
    )
    arg_parser.add_argument(
        "--time-limit",
        "-t",
        type=int,
        default=30,
        help="Time limit for the solver in seconds.",
    )
    arg_parser.add_argument(
        "--gap-limit",
        "-g",
        type=float,
        default=0.01,
        help="Relative gap limit for the solver.",
    )
    args = arg_parser.parse_args()
    if not args.layout.exists():
        raise FileNotFoundError(f"Layout file not found: {args.layout}")

    _main(args.layout, args.time_limit, args.gap_limit)
