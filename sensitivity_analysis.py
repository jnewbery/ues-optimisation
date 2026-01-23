import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import matplotlib.pyplot as plt

    # Data Setup
    scenarios = ['Baseline', 'Scenario 1', 'Scenario 2', 'Scenario 3']
    # Format: [Base/Median, Min (0.5x), Max (1.5x)]
    base_vals = [61313473, 100975026, 102255722, 100817542]
    max_vals = [88329709, 136827467, 136877737, 127745776]
    min_vals = [34297236, 65122584, 67633707, 73889308]

    # Calculate the error amounts for the whiskers
    # format: [lower_offset, upper_offset]
    lower_error = [b - m for b, m in zip(base_vals, min_vals)]
    upper_error = [mx - b for b, mx in zip(base_vals, max_vals)]
    asymmetric_error = [lower_error, upper_error]

    plt.figure(figsize=(10, 5))

    # Create continuous whiskers with a cap
    # fmt='_' creates a horizontal line at the median
    plt.errorbar(scenarios, base_vals, yerr=asymmetric_error, fmt='_', 
                 ecolor='#1f77b4', elinewidth=2, capsize=10, 
                 markeredgecolor='#d62728', markeredgewidth=4, markersize=25)

    # Formatting
    plt.title('TOTEX Sensitivity: Range and Median', fontsize=14)
    plt.ylabel('TOTEX (£)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # Format y-axis to Millions
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x*1e-6:.0f}M'))

    plt.tight_layout()
    plt.show()
    return


if __name__ == "__main__":
    app.run()
