"""Tools for the data_analyst agent.

Conventions (same for every agent):
- build_tools(cfg) returns (list_of_tools, cleanup_fn_or_None).
- The docstring is what the model reads: say what the tool does, when to use it, and what it returns.
- Return short strings. Return errors as text instead of raising.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from anthropic import beta_tool

from core.config import ROOT, AgentConfig
from core.sandbox import PythonSandbox

DATA_DIR = ROOT / "data"
SUPPORTED = {".csv", ".parquet", ".tsv", ".json", ".xlsx"}


def _safe_data_path(path: str) -> Path:
    p = Path(path)
    p = (p if p.is_absolute() else ROOT / p).resolve()
    if DATA_DIR.resolve() not in p.parents:
        raise ValueError(f"Path must be inside {DATA_DIR}")
    return p


def _read(p: Path) -> pd.DataFrame:
    match p.suffix:
        case ".parquet": return pd.read_parquet(p)
        case ".tsv": return pd.read_csv(p, sep="\t")
        case ".json": return pd.read_json(p)
        case ".xlsx": return pd.read_excel(p)
        case _: return pd.read_csv(p)


def build_tools(cfg: AgentConfig):
    out_dir = cfg.output_dir
    sandbox = PythonSandbox(
        cwd=str(ROOT),
        setup_code=(
            "import pandas as pd, numpy as np, matplotlib\n"
            "matplotlib.use('Agg')\n"
            "import matplotlib.pyplot as plt, seaborn as sns\n"
            "from pathlib import Path\n"
            f"DATA_DIR = Path(r'{DATA_DIR}')\nOUT_DIR = Path(r'{out_dir}')\n"
            "pd.set_option('display.width', 200); pd.set_option('display.max_columns', 50)\n"
        ),
    )

    @beta_tool
    def list_files() -> str:
        """List the dataset files available in the data directory, with sizes.
        Use this first to discover what data exists."""
        files = [p for p in DATA_DIR.rglob("*") if p.is_file() and p.suffix in SUPPORTED]
        if not files:
            return f"No data files found in {DATA_DIR}."
        return "\n".join(f"{p.relative_to(ROOT)}  ({p.stat().st_size / 1e6:.2f} MB)" for p in sorted(files))

    @beta_tool
    def profile_dataset(path: str) -> str:
        """Profile a dataset: shape, column dtypes, missing values, unique counts,
        numeric summary statistics, and the first rows. Use on any new file before analysis.

        Args:
            path: File path inside the data directory, e.g. data/sales.csv.
        """
        try:
            df = _read(_safe_data_path(path))
        except Exception as e:
            return f"Error reading {path}: {e}"
        cols = pd.DataFrame({
            "dtype": df.dtypes.astype(str),
            "missing_%": (df.isna().mean() * 100).round(1),
            "n_unique": df.nunique(),
        })
        return (
            f"shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n"
            f"duplicate rows: {df.duplicated().sum():,}\n\n"
            f"columns:\n{cols.head(60).to_string()}\n\n"
            f"numeric summary:\n{df.describe().T.round(3).head(40).to_string()}\n\n"
            f"first rows:\n{df.head(5).to_string()}"
        )[:8000]

    @beta_tool
    def run_python(code: str) -> str:
        """Run Python code in a persistent Jupyter kernel and return its printed output.
        Variables persist between calls. Preloaded: pd, np, plt, sns, DATA_DIR, OUT_DIR.
        Print results explicitly. Save plots to OUT_DIR (never plt.show()).
        Output longer than ~8000 characters is truncated.

        Args:
            code: Python code to execute.
        """
        return sandbox.run(code)

    @beta_tool
    def save_report(markdown: str, filename: str = "report.md") -> str:
        """Save the final analysis report as a Markdown file in the output directory.
        Call once, at the end, with the complete report.

        Args:
            markdown: The full report in Markdown.
            filename: File name, default report.md.
        """
        target = (out_dir / Path(filename).name).with_suffix(".md")
        target.write_text(markdown)
        return f"Report saved to {target}"

    return [list_files, profile_dataset, run_python, save_report], sandbox.close
