import base64
import io

import imageio.v2 as imageio
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import HTML

from digital_experiments.optmization import SEARCH_MODE, Modes
from digital_experiments.querying import experiments_for, to_dataframe


def get_blocks(arr):
    blocks = []
    start_idx = 0
    for idx in range(len(arr) - 1):
        a, b = arr[idx], arr[idx + 1]
        if a != b:
            blocks.append((arr[idx], (start_idx, idx)))
            start_idx = idx + 1
    blocks.append((arr[-1], (start_idx, len(arr) - 1)))
    return blocks


_colours = {
    Modes.MANUAL: "black",
    Modes.RANDOM: "blue",
    Modes.BAYESIAN: "red",
}


def track_minimization(root, loss=None):
    if loss is None:
        loss = lambda x: x

    experiments = experiments_for(root)

    results = [e.result for e in experiments]
    losses = [loss(out) for out in results]
    n = range(1, len(experiments) + 1)

    plt.plot(n, losses, "-k+", alpha=0.5)
    contexts = [e.metadata.get(SEARCH_MODE, Modes.MANUAL) for e in experiments]
    contexts = [c if pd.notna(c) else Modes.MANUAL for c in contexts]

    blocks = get_blocks(contexts)

    in_legend = {}
    for context, (start, end) in blocks:
        if context not in in_legend:
            in_legend[context] = True
            label = context.replace("-", " ").title()
        else:
            label = None

        plt.axvspan(
            start + 0.5,
            end + 1.5,
            alpha=0.2,
            label=label,
            color=_colours[context],
            linewidth=0,
        )
    plt.xlim(0.5, len(losses) + 0.5)

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=3)
    plt.plot(
        n,
        pd.Series(losses).cummin(),
        "-k",
        markersize=4,
        label="Best So Far",
    )
    plt.xlabel("Iteration")


def legend_outside(ax):
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))


def track_trials(x, y, root, callback=None, **kwargs):
    experiments = experiments_for(root)
    df = to_dataframe(experiments, metadata=True)
    df[f"metadata.{SEARCH_MODE}"].fillna(Modes.MANUAL, inplace=True)

    # experiments = convert_to_experiments(df)
    xs = [e.config[x] for e in experiments]
    ys = [e.config[y] for e in experiments]
    colours = df[f"metadata.{SEARCH_MODE}"].map(_colours)

    def _plot(i):
        plt.scatter(xs[:i], ys[:i], c=colours[:i], s=20, linewidths=0, clip_on=False)
        for mode in df[f"metadata.{SEARCH_MODE}"].unique():
            plt.scatter([], [], c=_colours[mode], label=mode.replace("-", " ").title())
        plt.xlabel(x)
        plt.ylabel(y)
        if callback is not None:
            callback(i)
        legend_outside(plt.gca())

    return gif(_plot, range(len(df) + 1), **kwargs)


def gif(plot_func, frames, name="mygif.gif", **kwargs):
    with imageio.get_writer(name, mode="I", **kwargs) as writer:
        for i in frames:
            plot_func(i)

            tmp_file = io.BytesIO()
            plt.savefig(tmp_file, bbox_inches="tight")
            plt.clf()

            tmp_file.seek(0)
            image = imageio.imread(tmp_file)
            writer.append_data(image)

    with open(name, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return HTML(f'<img src="data:image/gif;base64,{b64}" width=480px/>')
