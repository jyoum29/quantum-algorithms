"""Entry point for the quantum-algorithms analysis.

Usage:
    python main.py

Comment / uncomment plot calls below to choose which figures to generate.
All PNGs land directly in Plots/. Two visual styles are produced:

    parallel-algorithms style (default) - dtontici/parallel-algorithms
        look: compact figure, pastel single-series fill, horizontal
        multi-line ylabel, no cumulative overlay. Year + decade variants.
        File names: <plot>_per_year.png, <plot>_per_decade.png

    classic style - the original look from the first iteration of this
        repo: larger 10 x 5 figure, distinct primary colours, faint grid,
        cumulative line on a twinned y-axis, vertical ylabel. Year-binned
        only. File names: <plot>_per_year_classic.png
"""
from __future__ import annotations

from src.data_loader import build_processed_dataset
from src.header import PLOTS_DIR
from src.helpers import report_problems_coverage
from src.plots.family_improvements_per_year import plot_family_improvements_per_year
from src.plots.improvements_per_year import plot_improvements_per_year
from src.plots.problems_per_year import plot_problems_per_year


def main() -> None:
    print("[1/2] (Re)building cleaned dataset cache from the AlgoWiki workbook ...")
    qdf, pdf = build_processed_dataset()
    print(f"      quantum algorithms : {len(qdf):>4} rows, "
          f"{qdf.groupby(['family','variation']).ngroups} problems, "
          f"{qdf['family'].nunique()} families")
    print(f"      problems sheet     : {len(pdf):>4} rows")
    report_problems_coverage(qdf, pdf)

    print(f"\n[2/2] Generating plots into {PLOTS_DIR} ...")

    # ---------- Parallel-algorithms style (year + decade variants) -------
    print("\n  >>> parallel-algorithms style")
    plot_problems_per_year(by="problem", bin_by="year",   style="parallel")
    plot_problems_per_year(by="problem", bin_by="decade", style="parallel")
    plot_problems_per_year(by="family",  bin_by="year",   style="parallel")
    plot_problems_per_year(by="family",  bin_by="decade", style="parallel")
    plot_improvements_per_year(bin_by="year",   style="parallel")
    plot_improvements_per_year(bin_by="decade", style="parallel")
    plot_family_improvements_per_year(bin_by="year",   style="parallel")
    plot_family_improvements_per_year(bin_by="decade", style="parallel")
    plot_family_improvements_per_year(bin_by="year",   style="parallel", as_fraction=True)
    plot_family_improvements_per_year(bin_by="decade", style="parallel", as_fraction=True)

    # ---------- Classic style (original look, year-binned) ---------------
    print("\n  >>> classic style  (filenames carry a _classic suffix)")
    plot_problems_per_year(by="problem", style="classic")
    plot_problems_per_year(by="family",  style="classic")
    plot_improvements_per_year(style="classic")
    plot_family_improvements_per_year(style="classic")
    plot_family_improvements_per_year(style="classic", as_fraction=True)

    print("\nDone.")


if __name__ == "__main__":
    main()
