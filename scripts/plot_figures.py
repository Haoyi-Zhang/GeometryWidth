#!/usr/bin/env python3
"""Draw the retained exact four-point oracle with optional Matplotlib.

Run: python scripts/plot_figures.py [--data path/to/oracle_plot.csv]
Computer Modern Roman is bundled with Matplotlib and matches this JMLR paper.
The 49 plotted rows are checked against retained oracle.csv rational energies
and their closed form; neither certificates nor experiments are regenerated.
Native output: figures/oracle.pdf, 378 x 158 PDF points; identical bytes are
copied to sibling paper/figures when present.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import shutil

import matplotlib as mpl
mpl.use("Agg")
from matplotlib import font_manager as fm
from matplotlib import pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def configure_font() -> str:
    # Matplotlib bundles this genuine Computer Modern Roman face.
    path = Path(mpl.get_data_path()) / "fonts/ttf/cmr10.ttf"
    if not path.is_file():
        raise FileNotFoundError(path)
    fm.fontManager.addfont(str(path))
    family = fm.FontProperties(fname=str(path)).get_name()
    mpl.rcParams.update({
        "font.family": family, "font.size": 10, "mathtext.fontset": "cm",
        "pdf.fonttype": 42, "pdf.use14corefonts": False, "text.usetex": False,
        "axes.unicode_minus": False, "axes.formatter.use_mathtext": True,
        "axes.linewidth": .5, "path.simplify": False,
    })
    return family


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "results/oracle_plot.csv")
    parser.add_argument("--exact-data", type=Path, default=ROOT / "results/oracle.csv")
    args = parser.parse_args()
    family = configure_font()
    from fractions import Fraction as F
    with args.data.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    with args.exact_data.open(newline="", encoding="utf-8-sig") as stream:
        exact = list(csv.DictReader(stream))
    if len(rows) != 49 or len(exact) != 49:
        raise ValueError("Expected all 49 retained rational oracle points")
    for k, (plotted, rational) in enumerate(zip(rows, exact)):
        u = F(rational["u"])
        a = 1 + 3 * u
        true = 4 * a * a + 8
        minimum = true if u <= F(1, 3) else F(8, 3) * (a + 1)**2
        if (u != F(k, 12) or F(rational["true_energy"]) != true or
                F(rational["minimum_energy"]) != minimum or
                float(plotted["u"]) != float(u) or
                float(plotted["energy_ratio"]) != float(minimum / true)):
            raise ValueError(f"Oracle row {k} differs from retained exact energies")
    fig = plt.figure(figsize=(378 / 72, 158 / 72))
    ax = fig.add_axes([44 / 378, 26 / 158, 327 / 378, 125 / 158])
    ax.plot([float(row["u"]) for row in rows],
            [float(row["energy_ratio"]) for row in rows], color="black",
            marker="o", ms=2.2, lw=.8, label="Exact oracle")
    ax.plot([0, 4], [2 / 3, 2 / 3], color="black", ls="--", lw=.8, label="Limit 2/3")
    ax.plot([1 / 3, 1 / 3], [.64, 1], color="black", ls=":", lw=.6)
    ax.text(.42, .84, r"$u$ = 1/3", va="center", fontsize=10)
    ax.set(xlim=(0, 4), ylim=(.64, 1.03), xlabel=r"$u$",
           ylabel="Minimum energy / true energy")
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_yticks([2 / 3, .75, .875, 1], ["2/3", "0.75", "0.875", "1"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2, width=.5, pad=2)
    ax.legend(loc="upper right", bbox_to_anchor=(.97, .97), frameon=False, fontsize=10)
    output = ROOT / "figures/oracle.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"Creator": None, "Producer": None, "CreationDate": None, "ModDate": None})
    plt.close(fig)
    paper = ROOT.parent / "paper/figures"
    if paper.is_dir():
        shutil.copyfile(output, paper / output.name)
    print(f"oracle: 49 retained exact-checked rows, closed recovery at u=1/3, limit 2/3; embedded {family}")


if __name__ == "__main__":
    main()
