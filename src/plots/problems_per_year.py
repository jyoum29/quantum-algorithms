"""Plot 1: number of distinct problems first tackled by a quantum algorithm
each year (or each decade).

A "problem" is a (Family Name, Variation) pair. The ``Quantum Algorithms``
sheet is the source of truth for which problems exist in our quantum dataset;
the ``Problems`` sheet is used to (a) verify which families/variations are
part of the canonical AlgoWiki problem list and (b) optionally restrict the
plot to that intersection via ``restrict_to_problems_sheet=True``.

Two styles are supported via the ``style`` parameter:
  * ``"parallel"`` (default) - matches dtontici/parallel-algorithms.
  * ``"classic"``  - the original look (larger figure, distinct primary
    colour, faint grid, cumulative line on a twin axis, vertical y-label).
The output PNG lands under ``Plots/parallel/`` or ``Plots/classic/``
respectively.
"""
from __future__ import annotations

from pathlib import Path

from ..data_loader import get_problems, get_quantum_algorithms
from ..helpers import (
    bar_simple,
    bar_with_cumulative,
    decade_counts,
    first_year_per_problem,
    get_style,
    make_figure,
    multiline_ylabel,
    restrict_to_known_problems,
    save_plot,
    style_decade_axis,
    style_year_axis,
    yearly_counts,
)


def plot_problems_per_year(*, by: str = "problem", bin_by: str = "year",
                           style: str = "parallel",
                           show_cumulative: bool | None = None,
                           restrict_to_problems_sheet: bool = False,
                           save_name: str | None = None) -> Path:
    """Bar chart of how many problems were first introduced each year/decade.

    Parameters
    ----------
    by:
        - ``"problem"``: count distinct (family, variation) pairs (default).
        - ``"family"``:  count distinct families.
    bin_by:
        ``"year"`` (default) or ``"decade"``.
    style:
        ``"parallel"`` (default) or ``"classic"``.
    show_cumulative:
        Overlay a cumulative-count line on a secondary y-axis. Defaults come
        from the chosen style (``False`` for parallel, ``True`` for classic).
    restrict_to_problems_sheet:
        If True, only count problems whose (family, variation) appears in the
        Problems sheet.
    """
    s = get_style(style)
    if show_cumulative is None:
        show_cumulative = s["show_cumulative"]

    qdf = get_quantum_algorithms()
    problems = get_problems()
    if restrict_to_problems_sheet:
        qdf = restrict_to_known_problems(qdf, problems)

    if by == "problem":
        firsts = first_year_per_problem(qdf)
        ylabel_lines = ["Problems", "introduced"]
        title_unit = "problems"
        default_name_root = "problems_introduced"
    elif by == "family":
        firsts = first_year_per_problem(qdf, group_cols=("family",))
        ylabel_lines = ["Problem", "families", "introduced"]
        title_unit = "problem families"
        default_name_root = "families_introduced"
    else:
        raise ValueError(f"Unknown `by`: {by!r}")

    fig, ax = make_figure(figsize=s["figsize"], dpi=s["dpi"])
    color = s["color_problems"]
    label = f"{title_unit.capitalize()} introduced"
    if bin_by == "year":
        counts = yearly_counts(firsts["first_year"])
        if show_cumulative:
            bar_with_cumulative(ax, counts, color=color, label=label)
        else:
            bar_simple(ax, counts, color=color)
        style_year_axis(ax, grid_alpha=s["grid_alpha"])
        ax.set_xlabel("Year")
        suffix = "per_year"
    elif bin_by == "decade":
        counts = decade_counts(firsts["first_year"])
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
        multiline_ylabel(ax, ylabel_lines)
        ax.set_title(f"Quantum-tackled {title_unit} introduced over time")
    else:
        ax.set_ylabel(" ".join(ylabel_lines).capitalize())
        ax.set_title(f"Quantum-tackled {title_unit} introduced per "
                     f"{bin_by}")
    fig.tight_layout()

    save_name = save_name or f"{default_name_root}_{suffix}"
    out = save_plot(fig, save_name, save_dir=s["save_subdir"])
    print(f"  - {out.relative_to(out.parents[1])}  "
          f"({int(counts.sum())} {title_unit} total)")
    return out
