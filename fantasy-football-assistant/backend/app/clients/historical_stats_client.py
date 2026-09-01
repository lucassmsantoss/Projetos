"""Historical NFL stats via nfl_data_py (public, free, community-maintained
mirror of nflverse data). Used to compute last-season fantasy performance
independent of any single projection source.
"""
from __future__ import annotations

import pandas as pd


def load_seasonal_fantasy_stats(season: int) -> pd.DataFrame:
    """Returns one row per player for the given season with PPR fantasy points."""
    import nfl_data_py as nfl

    df = nfl.import_seasonal_data([season], s_type="REG")
    df = df.rename(
        columns={
            "player_id": "gsis_id",
            "fantasy_points_ppr": "fantasy_points_ppr",
            "games": "games_played",
        }
    )
    df["fantasy_points_per_game_ppr"] = df["fantasy_points_ppr"] / df["games_played"].replace(0, pd.NA)
    return df[
        [
            "gsis_id",
            "games_played",
            "fantasy_points_ppr",
            "fantasy_points_per_game_ppr",
            "targets",
            "receptions",
            "rushing_att",
            "attempts",
            "receiving_tds",
            "rushing_tds",
            "passing_tds",
        ]
    ]


def load_player_id_map() -> pd.DataFrame:
    """Maps gsis_id (used by nfl_data_py) to sleeper player IDs."""
    import nfl_data_py as nfl

    ids = nfl.import_ids()
    return ids[["gsis_id", "sleeper_id", "name"]].dropna(subset=["gsis_id"])
