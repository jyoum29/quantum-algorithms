"""Plot 3: number of *problem families* that received at least one improvement
each year (or each decade).

Same improvement definition as plot 2, but rolled up to the family level: in
a given period, count one tally per family that had any improvement event in
any of its variations during that period. With ``as_fraction=True`` the bars
become a percentage of all quantum families - this is the closest analogue
to parallel-algorithms' ``decade_progress.py::average_improvement_over_decade_graph``,
which renders ``"% Problem Families with Improvements"`` by decade.

Two styles are supported via the ``style`` parameter:
  * ``"parallel"`` (default) - matches dtontici/parallel-algorithms.
  * ``"classic"``  - the original look (cumulative line on a twin axis,
    larger figure, distinct primary colour, faint grid, vertical y-label).
"""
from __future__ import annotations

from pathlib import Path

from ..data_loader import get_problems, get_quantum_algorithms
from ..helpers import (
    bar_simple,
    bar_with_cumulative,
    decade_unique,
    get_style,
    make_figure,
    mark_improvements,
    multiline_ylabel,
    percent_yaxis,
    restrict_to_known_problems,
    save_plot,
    style_decade_axis,
    style_year_axis,
    yearly_counts,
)


def plot_family_improvements_per_year(*, bin_by: str = "year",
                                      style: str = "parallel",
                                      include_first: bool = False,
                                      show_cumulative: bool | None = None,
                                      as_fraction: bool = False,
                                      restrict_to_problems_sheet: bool = False,
                                      save_name: str | None = None) -> Path:
    """Bar chart of how many families saw an improvement each year/decade.

    Parameters
    ----------
    bin_by:
        ``"year"`` (default) or ``"decade"``.
    style:
        ``"parallel"`` (default) or ``"classic"``.
    include_first:
        If True, the first algorithm for any variation also counts as an
        improvement for its family.
    show_cumulative:
        Defaults come from the chosen style; cumulative line is suppressed
        whenever ``as_fraction=True`` because the fraction y-axis already
        has a fixed scale.
    as_fraction:
        If True, show the y-axis as a percentage of all families that have at
        least one quantum algorithm in our dataset.
    restrict_to_problems_sheet:
        If True, only consider problems whose (family, variation) appears in
        the Problems sheet.
    """
    s = get_style(style)
    if show_cumulative is None:
        show_cumulative = s["show_cumulative"]
    if as_fraction:
        show_cumulative = False

    qdf = get_quantum_algorithms()
    problems = get_problems()
    if restrict_to_problems_sheet:
        qdf = restrict_to_known_problems(qdf, problems)

    annotated = mark_improvements(qdf)
    if include_first:
        improvements = annotated[annotated["is_improvement"]]
    else:
        improvements = annotated[
            annotated["is_improvement"] & ~annotated["is_first"]
        ]
    n_families = qdf["family"].nunique()

    fig, ax = make_figure(figsize=s["figsize"], dpi=s["dpi"])
    color = s["color_families"]
    label = "Families improved"
    if bin_by == "year":
        family_year = improvements[["family", "year"]].dropna().drop_duplicates()
        counts = yearly_counts(family_year["year"])
        if as_fraction:
            counts = counts / max(n_families, 1) * 100.0
        if show_cumulative:
            bar_with_cumulative(ax, counts, color=color, label=label)
        else:
            bar_simple(ax, counts, color=color)
        style_year_axis(ax, integer_y=not as_fraction, grid_alpha=s["grid_alpha"])
        ax.set_xlabel("Year")
        suffix = "per_year"
    elif bin_by == "decade":
        counts = decade_unique(improvements, year_col="year", key_cols=("family",))
        if as_fraction:
            counts = counts / max(n_families, 1) * 100.0
        if show_cumulative:
            bar_with_cumulative(ax, counts, color=color, label=label)
        else:
            bar_simple(ax, counts, color=color)
        style_decade_axis(ax, integer_y=not as_fraction, grid_alpha=s["grid_alpha"])
        ax.set_xlabel("Decade")
        suffix = "per_decade"
    else:
        raise ValueError(f"Unknown `bin_by`: {bin_by!r}")

    if as_fraction:
        percent_yaxis(ax)

    if s["horizontal_ylabel"]:
        if as_fraction:
            multiline_ylabel(ax, ["% Problem", "Families with", "Improvements"])
            ax.set_title("Algorithm improvements over time")
        else:
            multiline_ylabel(ax, ["Families", "improved"])
            ax.set_title("Problem families with improvements over time")
    else:
        if as_fraction:
            ax.set_ylabel("Fraction of families improved")
            ax.set_title(f"Share of quantum families improved per {bin_by}")
        else:
            ax.set_ylabel(label)
            ax.set_title(f"Problem families with improvements per {bin_by}")
    fig.tight_layout()

    save_root = "family_improvements_fraction" if as_fraction else "family_improvements"
    save_name = save_name or f"{save_root}_{suffix}{s['name_suffix']}"
    out = save_plot(fig, save_name, save_dir=s["save_subdir"])
    if as_fraction:
        print(f"  - {out.relative_to(out.parent.parent)}  "
              f"(peak share = {counts.max():.1f}%)")
    else:
        print(f"  - {out.relative_to(out.parent.parent)}  "
              f"({int(counts.sum())} family-improvement-{bin_by}s total)")
    return out
