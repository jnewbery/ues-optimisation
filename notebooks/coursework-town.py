import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo

    from src.town_rendering import render_town_layout

    return Path, mo, render_town_layout


@app.cell
def _():
    town_layout = [
        ["20", "20", "20", "20", "20", "20", "G", "20", "20", "H", "H", "H"],
        ["20", "30", "30", "30", "30", "30", "G", "20", "20", "H", "H", "H"],
        ["20", "30", "G", "G", "30", "30", "G", "G", "G", "G", "G", "20"],
        ["20", "30", "30", "30", "30", "30", "G", "G", "G", "G", "G", "20"],
        ["20", "30", "40", "40", "40", "40", "30", "30", "30", "30", "G", "20"],
        ["20", "30", "G", "G", "SC", "SC", "30", "30", "30", "30", "G", "20"],
        ["20", "30", "EC", "O", "SC", "SC", "O", "30", "30", "30", "30", "20"],
        ["20", "O", "EC", "O", "SC", "SC", "O", "20", "20", "20", "20", "20"],
        ["20", "O", "O", "O", "SC", "SC", "O", "O", "EC", "EC", "O", "20"],
        ["20", "20", "O", "O", "OF", "OF", "O", "O", "O", "O", "O", "20"],
        ["20", "20", "20", "20", "OF", "OF", "O", "SCH", "SCH", "G", "G", "20"],
        ["EC", "EC", "20", "20", "20", "20", "O", "SCH", "SCH", "G", "G", "20"],
        ["EC", "EC", "20", "20", "30", "30", "20", "20", "G", "G", "G", "20"],
    ]
    return (town_layout,)


@app.cell
def _(Path, mo, render_town_layout, town_layout):
    image_dir = Path("notebooks") / "img"
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
