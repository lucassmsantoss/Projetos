"""Builds a training set from multiple past seasons: for each season N,
use players' season N-1 (pre-season-known) stats as features and their
actual season N PPR points-per-game as the label. Feeds PlayerValueModel.
"""
from __future__ import annotations

import pandas as pd

from app.ml.value_model import FEATURE_COLUMNS, TARGET_COLUMN


def build_training_set(seasons: list[int]) -> pd.DataFrame:
    """`seasons` are the *target* seasons to predict (e.g. [2022,2023,2024,2025]);
    for each we pull season-1 as the feature snapshot and season as the label.
    """
    import nfl_data_py as nfl

    all_years = sorted({s - 1 for s in seasons} | set(seasons))
    seasonal = nfl.import_seasonal_data(all_years, s_type="REG")
    seasonal["ppg"] = seasonal["fantasy_points_ppr"] / seasonal["games"].replace(0, pd.NA)

    rows = []
    for season in seasons:
        prev = seasonal[seasonal["season"] == season - 1].set_index("player_id")
        curr = seasonal[seasonal["season"] == season].set_index("player_id")
        common_ids = prev.index.intersection(curr.index)
        for pid in common_ids:
            p = prev.loc[pid]
            c = curr.loc[pid]
            rows.append(
                {
                    "age": None,
                    "years_exp": None,
                    "injury_risk": 0.0,
                    "last_season_ppg": p.get("ppg") or 0,
                    "last_season_games": p.get("games") or 0,
                    "projected_ppg": p.get("ppg") or 0,  # no historical projection archive; use prior PPG as proxy
                    "projected_points": p.get("fantasy_points_ppr") or 0,
                    "ecr_rank": None,
                    "ecr_position_rank": None,
                    "adp": None,
                    TARGET_COLUMN: c.get("ppg") or 0,
                }
            )

    df = pd.DataFrame(rows)
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0
    return df
