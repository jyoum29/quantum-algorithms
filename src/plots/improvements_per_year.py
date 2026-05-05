"""Plot 2: number of algorithmic improvement events per year (or decade).

An *improvement event* for a problem (family, variation) is any algorithm
whose ``Time Complexity Class`` is strictly lower than the best class
previously seen for that problem (lower class = faster, per the AlgoWiki
encoding). The very first algorithm for a problem is treated as introducing
the problem and excluded from this plot - those are tracked separately by
plot 1.

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
    decade_counts,
    get_style,
    make_figure,
    mark_improvements,
    multiline_ylabel,
    restrict_to_known_problems,
    save_plot,
    style_decade_axis,
    style_year_axis,
    yearly_counts,
)


def plot_improvements_per_year(*, bin_by: str = "year",
                               style: str = "parallel",
                               include_first: bool = False,
                               show_cumulative: bool | None = None,
                               restrict_to_problems_sheet: bool = False,
                               save_name: str | None = None) -> Path:
    """Bar chart of yearly (or decadal) improvement counts.

    Parameters
    ----------
    bin_by:
        ``"year"`` (default) or ``"decade"``.
    style:
        ``"parallel"`` (default) or ``"classic"``.
    include_first:
        If True, also count the first algorithm for each problem (which is
        the problem-introduction event).
    show_cumulative:
        Defaults come from the chosen style.
    restrict_to_problems_sheet:
        If True, only consider problems whose (family, variation) appears in
        the Problems sheet.
    """
    s = get_style(style)
    if show_cumulative is None:
        show_cumulative = s["show_cumulative"]

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

    fig, ax = make_figure(figsize=s["figsize"], dpi=s["dpi"])
    color = s["color_improvements"]
    label = "Improvement events"
    if bin_by == "year":
        counts = yearly_counts(improvements["year"])
        if show_cumulative:
            bar_with_cumulative(ax, counts, color=color, label=label)
        else:
            bar_simple(ax, counts, color=color)
        style_year_axis(ax, grid_alpha=s["grid_alpha"])
        ax.set_xlabel("Year")
        suffix = "per_year"
    elif bin_by == "decade":
        counts = decade_counts(improvements["year"])
        if show_cumulative:
            bar_with_cumulative(ax, counts, color=color, label=label)
        else:
            bar_simple(ax, counts, color=color)
        style_decade_axis(ax, grid_alpha=s["grid_alpha"])
        ax.set_xlabel("Decade")
        suffix = "per_decade"
    else:
        raise ValueError(f"Unknown `bin_by`: {bin_by!r}")

    if s["horizontal_ylabel"]:
        multiline_ylabel(ax, ["Improvement", "events"])
        ax.set_title("Algorithm improvements over time")
    else:
        ax.set_ylabel(label)
        ax.set_title(f"Algorithmic improvement events per {bin_by}")
    fig.tight_layout()

    save_name = save_name or f"improvements_{suffix}"
    out = save_plot(fig, save_name, save_dir=s["save_subdir"])
    print(f"  - {out.relative_to(out.parents[1])}  "
          f"({int(counts.sum())} improvement events total)")
    return out
