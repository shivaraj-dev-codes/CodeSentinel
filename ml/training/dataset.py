"""Dataset utilities — download and prepare the Big-Vul / Devign dataset."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_bigvul(path: str | Path) -> pd.DataFrame:
    """
    Load the Big-Vul dataset.

    The Big-Vul dataset is available at:
    https://github.com/ZeoVan/MSR_20_Code_vulnerability_CSV_Dataset

    Expected columns: func, target (1=vulnerable, 0=safe), CWE_ID
    """
    df = pd.read_parquet(str(path))
    logger.info("Loaded Big-Vul dataset: %d rows, %d columns", *df.shape)
    return df


def load_devign(path: str | Path) -> pd.DataFrame:
    """
    Load the Devign dataset.

    The Devign dataset is available at:
    https://sites.google.com/view/devign

    Expected columns: func, target (1=vulnerable, 0=safe), project
    """
    df = pd.read_json(str(path))
    logger.info("Loaded Devign dataset: %d rows", len(df))
    return df


def prepare_python_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and filter a dataset to Python-only entries.

    - Removes entries with missing code or labels
    - Filters to Python language entries (if language column present)
    - Deduplicates by function content
    - Truncates very long functions to 1000 lines to avoid memory issues
    """
    df = df.dropna(subset=["func", "target"]).copy()
    df["target"] = df["target"].astype(int)

    if "language" in df.columns:
        df = df[df["language"].str.lower().isin(["python", "py"])].copy()

    # Deduplicate
    before = len(df)
    df = df.drop_duplicates(subset=["func"]).reset_index(drop=True)
    logger.info("Deduplication: %d → %d rows", before, len(df))

    # Truncate very long functions
    df["func"] = df["func"].apply(lambda x: "\n".join(str(x).splitlines()[:1000]))

    return df


def get_sample_dataset() -> pd.DataFrame:
    """
    Return a small synthetic dataset for smoke-testing the training pipeline.
    NOT for production use — accuracy will be meaningless on this data.
    """
    import numpy as np

    rng = np.random.default_rng(42)

    vulnerable_samples = [
        "def query(table):\n    conn.execute(f'SELECT * FROM {table}')",
        "def run(cmd):\n    import os\n    os.system(cmd)",
        "def load(data):\n    import pickle\n    return pickle.loads(data)",
        "import yaml\ndef config(f):\n    return yaml.load(f)",
        "def auth(p):\n    password = 'admin123'\n    return p == password",
        "def hash(p):\n    import hashlib\n    return hashlib.md5(p.encode())",
        "import subprocess\ndef shell(cmd):\n    subprocess.run(cmd, shell=True)",
        "def token():\n    import random\n    return random.random()",
        "def catch():\n    try:\n        pass\n    except:\n        pass",
    ]

    safe_samples = [
        "def query(table: str) -> list:\n    return db.session.execute(select(User)).all()",
        "def run(args: list) -> int:\n    return subprocess.run(args, check=True).returncode",
        "def load(path: Path) -> dict:\n    return json.loads(path.read_text())",
        "def config(f) -> dict:\n    return yaml.safe_load(f)",
        "def verify(password, hashed) -> bool:\n    return bcrypt.checkpw(password, hashed)",
        "def hash(data: bytes) -> str:\n    return hashlib.sha256(data).hexdigest()",
        "def shell(args: list) -> str:\n    return subprocess.check_output(args).decode()",
        "def token() -> str:\n    import secrets\n    return secrets.token_hex(32)",
        "def fetch(url: str) -> dict:\n    resp = requests.get(url, timeout=5)\n    resp.raise_for_status()\n    return resp.json()",
    ]

    # Multiply to get a usable dataset size
    vulnerable = vulnerable_samples * 20
    safe = safe_samples * 60

    funcs = vulnerable + safe
    targets = [1] * len(vulnerable) + [0] * len(safe)

    # Shuffle
    idx = rng.permutation(len(funcs))
    funcs = [funcs[i] for i in idx]
    targets = [targets[i] for i in idx]

    return pd.DataFrame({"func": funcs, "target": targets})
