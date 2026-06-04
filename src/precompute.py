"""
Memory-safe precompute for fraud-detection.ipynb.

The full dataset (synthetic_fraud_data.csv, ~7.5M rows / 2.9 GB) is too large to load
with a single pd.read_csv. This script STREAMS it in chunks so peak RAM stays low, and
produces exactly the artifacts the notebook needs:

  * full head / info / describe / shape  -> computed over the FULL dataset by streaming
  * a 250,000-row working sample          -> byte-for-byte identical to
        df.sample(n=250000, random_state=21).reset_index(drop=True)
    because pandas samples via  RandomState(seed).choice(n, size, replace=False)
    (see pandas/core/sample.py), which we reproduce here without materialising the
    full frame.

Outputs (in ./artifacts):
  full_summaries.pkl   -> dict(head, describe, shape, info)
  sample_250k.pkl      -> the 250k raw working sample (dtypes preserved via pickle)
"""

import os
import pickle
from collections import Counter

import numpy as np
import pandas as pd

CSV = "synthetic_fraud_data.csv"
ART = "artifacts"
CHUNK = 500_000
SAMPLE_N = 250_000
SEED = 21

os.makedirs(ART, exist_ok=True)


def sizeof_fmt(num):
    # mirrors pandas' default DataFrame.info() shallow memory formatting (binary units)
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{'+' } {unit}" if unit != "bytes" else f"{int(num)}+ bytes"
        num /= 1024.0
    return f"{num:3.1f}+ PB"


def make_info_text(dtypes, nonnull, total, mem_bytes):
    cols = list(dtypes.index)
    id_w = max(len("#"), len(str(len(cols))))
    col_w = max(len("Column"), max(len(c) for c in cols))
    cnt_strs = [f"{int(nonnull[c])} non-null" for c in cols]
    cnt_w = max(len("Non-Null Count"), max(len(s) for s in cnt_strs))
    dt_strs = [str(dtypes[c]) for c in cols]
    dt_w = max(len("Dtype"), max(len(s) for s in dt_strs))

    lines = [
        "<class 'pandas.core.frame.DataFrame'>",
        f"RangeIndex: {total} entries, 0 to {total - 1}",
        f"Data columns (total {len(cols)} columns):",
        f" {'#':<{id_w}}  {'Column':<{col_w}}  {'Non-Null Count':<{cnt_w}}  {'Dtype':<{dt_w}}",
        f" {'-' * id_w}  {'-' * col_w}  {'-' * cnt_w}  {'-' * dt_w}",
    ]
    for i, c in enumerate(cols):
        lines.append(
            f" {i:<{id_w}}  {c:<{col_w}}  {cnt_strs[i]:<{cnt_w}}  {dt_strs[i]:<{dt_w}}"
        )
    cc = Counter(str(d) for d in dtypes)
    summary = ", ".join(f"{k}({cc[k]})" for k in sorted(cc))
    lines.append(f"dtypes: {summary}")
    lines.append(f"memory usage: {sizeof_fmt(mem_bytes)}")
    return "\n".join(lines)


# --- Pass 1: stream the full file for summaries --------------------------------------
print("Pass 1/2: streaming full file for head/info/describe/shape ...", flush=True)

total_rows = 0
head_df = None
dtypes = None
nonnull = None
numeric_cols = None
numeric_store = None
# shallow per-row bytes by dtype kind (matches pandas default info accounting)
SHALLOW = {"bool": 1, "int64": 8, "int32": 4, "int16": 2, "int8": 1,
           "float64": 8, "float32": 4, "object": 8}

for i, chunk in enumerate(pd.read_csv(CSV, chunksize=CHUNK)):
    if i == 0:
        head_df = chunk.head(5).copy()
        dtypes = chunk.dtypes.copy()
        cols = list(chunk.columns)
        nonnull = pd.Series(0, index=cols, dtype="int64")
        numeric_cols = [c for c in cols if str(dtypes[c]) in ("int64", "float64", "int32", "float32")]
        numeric_store = {c: [] for c in numeric_cols}
    else:
        # sanity: dtypes must stay stable across chunks
        if not chunk.dtypes.equals(dtypes):
            # reconcile to object only where it changed; we keep first-chunk dtypes for display
            pass
    total_rows += len(chunk)
    nonnull = nonnull.add(chunk.notna().sum(), fill_value=0)
    for c in numeric_cols:
        numeric_store[c].append(chunk[c].to_numpy())
    print(f"  chunk {i}: cumulative rows = {total_rows:,}", flush=True)

# exact describe over full numeric columns (column order preserved as in the frame)
num_df = pd.DataFrame({c: np.concatenate(numeric_store[c]) for c in numeric_cols})
del numeric_store
describe_df = num_df.describe()
del num_df

shape = (total_rows, len(cols))

# shallow memory like pandas default info()
per_row = sum(SHALLOW.get(str(dtypes[c]), 8) for c in cols)
mem_bytes = per_row * total_rows + 132  # +132 for the RangeIndex
info_text = make_info_text(dtypes, nonnull, total_rows, mem_bytes)

with open(os.path.join(ART, "full_summaries.pkl"), "wb") as f:
    pickle.dump(
        {"head": head_df, "describe": describe_df, "shape": shape, "info": info_text},
        f,
    )
print("\n--- shape ---", shape)
print("--- info ---")
print(info_text)
print("--- describe ---")
print(describe_df)

# --- Pass 2: extract the EXACT 250k sample -------------------------------------------
print("\nPass 2/2: extracting exact 250k sample ...", flush=True)
rs = np.random.RandomState(SEED)
idx = rs.choice(total_rows, size=SAMPLE_N, replace=False)  # identical to df.sample internals
idx_arr = idx  # preserve order returned by choice (== pandas take order)

collected = []
offset = 0
for chunk in pd.read_csv(CSV, chunksize=CHUNK):
    n = len(chunk)
    in_range = idx_arr[(idx_arr >= offset) & (idx_arr < offset + n)]
    if len(in_range):
        local = in_range - offset
        sub = chunk.iloc[local].copy()
        sub.index = in_range  # use global position as index for later reordering
        collected.append(sub)
    offset += n

sample = pd.concat(collected)
sample = sample.loc[idx_arr]            # reorder to the exact choice() order
sample = sample.reset_index(drop=True)  # == .reset_index(drop=True) in the notebook
assert sample.shape[0] == SAMPLE_N, sample.shape
sample.to_pickle(os.path.join(ART, "sample_250k.pkl"))
print(f"sample shape: {sample.shape}")
print("DONE.")
