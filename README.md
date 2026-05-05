# quantum-algorithms

Analysis pipeline that ingests AlgoWiki's Quantum Algorithms sheet and
produces plots about how quantum algorithms have been introduced and
improved over time. The structure mirrors:

- [dtontici/parallel-algorithms](https://github.com/dtontici/parallel-algorithms)
  (`header.py` for global config, `data/` for raw + processed data,
  `src/` for the analysis library, `main.py` to drive the plot calls)
- [andrewlucasgs/approximation-algorithms](https://github.com/andrewlucasgs/approximation-algorithms)
  (best-so-far improvement detection inside each problem)

## Repo layout

```text
quantum-algorithms/
|-- README.md
|-- requirements.txt
|-- main.py                            # comment/uncomment to choose plots
|-- data/
|   |-- AlgoWiki algorithms (our copy) (2).xlsx   # source spreadsheet
|   `-- processed/                     # cached cleaned outputs (CSV + JSON)
|-- src/
|   |-- header.py                      # paths, colors, year window
|   |-- data_loader.py                 # reads xlsx, cleans, caches
|   |-- helpers.py                     # improvement detection + plot styling
|   `-- plots/
|       |-- problems_per_year.py
|       |-- improvements_per_year.py
|       `-- family_improvements_per_year.py
`-- Plots/                             # generated PNGs land here
```

## Running

```bash
pip install -r requirements.txt
python main.py
```

The first run reads the `.xlsx` and writes
`data/processed/quantum_algos_v1.{json,csv}` and
`data/processed/problems_v1.{json,csv}`. Subsequent imports of the loader
read the cached CSVs (much faster than re-parsing the workbook).

## What the pipeline does

`src/data_loader.py` is the ETL stage:

1. Reads the `Quantum Algorithms` and `Problems` sheets.
2. Renames the verbose AlgoWiki columns to short snake_case keys
   (`Family Name` -> `family`, `Time Complexity Class` -> `time_class`, ...).
3. Title-cases family names so case mismatches like
   `'Integer factoring'` vs `'Integer Factoring'` collapse to a single key.
4. Drops rows the source flags as removed (`Looked at? == 0.001`)
   and rows missing a family or year.
5. Writes `quantum_algos_v1.{json,csv}` and `problems_v1.{json,csv}`.

`src/helpers.py::mark_improvements` then walks each problem
(default group key: `(family, variation)`) in chronological order and tags
every algorithm with:

- `is_first` - the earliest entry in the group (problem-introduction).
- `is_improvement` - strictly lower `Time Complexity Class` than the best
  seen so far in that group. The AlgoWiki convention is that lower
  complexity-class numbers mean faster algorithms.

## Plots

`python main.py` writes 15 PNGs directly under `Plots/`. The classic-style
files are tagged with a `_classic` suffix so the two styles can coexist in
the same folder:

```text
Plots/
|-- # parallel-algorithms style (default; year + decade variants)
|-- problems_introduced_per_year.png            problems_introduced_per_decade.png
|-- families_introduced_per_year.png            families_introduced_per_decade.png
|-- improvements_per_year.png                   improvements_per_decade.png
|-- family_improvements_per_year.png            family_improvements_per_decade.png
|-- family_improvements_fraction_per_year.png   family_improvements_fraction_per_decade.png
|
|-- # classic style (original look; year-binned only; _classic suffix)
|-- problems_introduced_per_year_classic.png
|-- families_introduced_per_year_classic.png
|-- improvements_per_year_classic.png
|-- family_improvements_per_year_classic.png
`-- family_improvements_fraction_per_year_classic.png
```

### Style differences

| Property | `parallel` (default) | `classic` |
|---|---|---|
| Figure size / DPI | 6.55 x 3.5 in @ 200 dpi (matches their `decade_progress.py`) | 10 x 5 in @ 150 dpi |
| Palette | Pastel `SEQ_PAR_COLORS = ['#F5C8AF', '#58D68D']` (peach + green) | Distinct primaries `#1f77b4` / `#2ca02c` / `#d62728` (blue / green / red) |
| Background | Clean white, no grid | Faint horizontal grid (`alpha=0.25`) |
| Y-label | Horizontal, multi-line (`% Problem\nFamilies with\nImprovements`) | Vertical, single-line |
| Cumulative line | Off (single axis) | On (drawn on a secondary y-axis with a legend) |
| Title style | "Algorithm improvements over time" | "Quantum-tackled problems introduced per year" |
| Bin granularity | Both year and decade variants | Year-binned only |

Both styles share the same underlying data, the same improvement-detection
algorithm, and the same join semantics with the Problems sheet - only the
visual rendering differs.

### Per-plot description

| Plot | What it shows |
|---|---|
| `problems_introduced_per_*.png`            | When a (family, variation) was first tackled by a quantum algorithm. |
| `families_introduced_per_*.png`            | When a *family* first saw any quantum algorithm. |
| `improvements_per_*.png`                   | Strict-class improvement events: a new algorithm whose Time Complexity Class beats the running best for that problem. |
| `family_improvements_per_*.png`            | Distinct families with at least one improvement event in the period. |
| `family_improvements_fraction_per_*.png`   | Same as above expressed as % of all quantum families - the direct analogue of parallel-algorithms' `par_vs_seq_imprv_thesis_weight.png`. |

## Adjusting things

- **Year window / colors / save location / decade buckets**: `src/header.py`
  (`MIN_YEAR`, `CUR_YEAR`, `DECADES`, `SEQ_PAR_COLORS`, `FIGSIZE`, `DPI`).
- **Which sheet version is loaded**: change `VERSION` in `src/header.py`
  and re-run; outputs land at `data/processed/quantum_algos<VERSION>.json`.
- **Which fields are kept from the workbook**: `QUANTUM_FIELDS` and
  `PROBLEMS_FIELDS` in `src/data_loader.py`.
- **What counts as an improvement**: change `metric_col` in calls to
  `mark_improvements` (e.g. swap `time_class` for `space_class`).
- **Style**: every plot accepts `style="parallel"` (default) or
  `style="classic"`. The style controls figure size, DPI, palette,
  cumulative-line behaviour, y-label orientation, and the output filename
  suffix (no suffix for `parallel`, `_classic` for `classic`). Add a new
  style by extending the `STYLES` dict in `src/header.py`.
- **Year vs decade binning**: every plot accepts `bin_by="year"` (default)
  or `bin_by="decade"` (matches parallel-algorithms' look exactly).
- **Cumulative line overlay**: every plot accepts `show_cumulative=True/False`
  to override the style default. Defaults: `False` for `parallel`, `True`
  for `classic`.
- **Restrict to canonical Problems-sheet entries only**: pass
  `restrict_to_problems_sheet=True` to any plot function. By default the
  Quantum Algorithms sheet defines scope; the Problems sheet is used only
  for join enrichment because ~half of the (family, variation) pairs in
  Quantum aren't present verbatim in Problems (different variation
  granularity, e.g. `'APSP (Adjacency Matrix Model)'`).

## Notes / caveats

- The `Final Call`, `Quantum?`, `Approximate?`, `Heuristic-based?` columns
  are sparsely populated in the source sheet, so we don't filter on them.
  `Looked at?` is the most reliable inclusion flag and we exclude rows
  with the AlgoWiki "explicitly removed" sentinel `0.001`.
- Improvement detection relies on `Time Complexity Class`, which is
  populated for ~67 % of rows. Rows missing the class are kept but cannot
  trigger an improvement.
- After cleaning we have ~205 algorithms across 88 problems / 48 families,
  spanning 1984 - 2026.

## License

Internal research code. Source data is the AlgoWiki spreadsheet.
