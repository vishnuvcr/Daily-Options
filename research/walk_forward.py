from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp

def expanding_windows(dates: Sequence[pd.Timestamp], train_size: int = 60, validation_size: int = 20, test_size: int = 20, embargo_size: int = 2, step_size: int = 20) -> list[WalkForwardWindow]:
    dates = pd.DatetimeIndex(sorted(pd.to_datetime(list(dates)).unique()))
    windows = []
    start = 0
    while True:
        train_end = start + train_size
        val_end = train_end + validation_size
        test_start = val_end + embargo_size
        test_end = test_start + test_size
        if test_end > len(dates):
            break
        windows.append(WalkForwardWindow(dates[start], dates[train_end - 1], dates[train_end], dates[val_end - 1], dates[test_start], dates[test_end - 1]))
        start += step_size
    return windows

def split_frame(frame: pd.DataFrame, window: WalkForwardWindow, date_column: str = 'date') -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    x = frame.copy()
    x[date_column] = pd.to_datetime(x[date_column])
    train = x[(x[date_column] >= window.train_start) & (x[date_column] <= window.train_end)]
    validation = x[(x[date_column] >= window.validation_start) & (x[date_column] <= window.validation_end)]
    test = x[(x[date_column] >= window.test_start) & (x[date_column] <= window.test_end)]
    return train, validation, test

def block_bootstrap_mean(values: Iterable[float], block_size: int = 5, iterations: int = 5000, seed: int = 42) -> dict[str, float]:
    x = np.asarray(list(values), dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {'mean': float('nan'), 'lower_95': float('nan'), 'upper_95': float('nan')}
    rng = np.random.default_rng(seed)
    block_size = max(1, min(int(block_size), len(x)))
    means = np.empty(iterations)
    for i in range(iterations):
        starts = rng.integers(0, len(x), size=int(np.ceil(len(x) / block_size)))
        sample = []
        for s in starts:
            sample.extend(x[(s + j) % len(x)] for j in range(block_size))
        means[i] = np.mean(sample[:len(x)])
    return {'mean': float(np.mean(x)), 'lower_95': float(np.quantile(means, 0.025)), 'upper_95': float(np.quantile(means, 0.975))}