from pathlib import Path

from layout import load_layout
from model import build_and_solve_model
from argparse import ArgumentParser

LAYOUT_DIR = Path("data")

def _main(layout_path: Path) -> None:
    town = load_layout(layout_path)

    optimisation_result = build_and_solve_model(
        town,
        cost_energy_center=2_000_000,
        cost_pipe=100_000,
        time_limit_seconds=30,
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
    args = arg_parser.parse_args()
    if not args.layout.exists():
        raise FileNotFoundError(f"Layout file not found: {args.layout}")

    _main(args.layout)
