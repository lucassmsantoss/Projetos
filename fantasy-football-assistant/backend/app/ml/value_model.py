"""Player value model.

Why gradient boosting instead of a neural network: our dataset is
tabular, has only a few hundred fantasy-relevant players per season, and
mixes very different feature types (rank-based, rate-based, categorical
position). Boosted trees (XGBoost) handle this shape with far less data
and tuning than a neural net needs to avoid overfitting, and they expose
feature_importances_ so we can show *why* a player is ranked where it is
— important for a tool you're trusting mid-draft. A small MLP is left as
`train_mlp_baseline` for comparison; swap it in via `MODEL_KIND=mlp` if
you want to A/B it once you have a few seasons of outcomes logged.

The model predicts each player's *actual* next-season PPR fantasy points
per game from pre-season inputs (projection, ECR, ADP, last season
performance, age/experience). Training data: nfl_data_py seasonal stats
across multiple past seasons, using season N-1 features to predict
season N outcomes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from xgboost import XGBRegressor

FEATURE_COLUMNS = [
    "age",
    "years_exp",
    "injury_risk",
    "last_season_ppg",
    "last_season_games",
    "projected_ppg",
    "projected_points",
    "ecr_rank",
    "ecr_position_rank",
    "adp",
]

TARGET_COLUMN = "actual_next_season_ppg"


class PlayerValueModel:
    def __init__(self, kind: str = "xgboost"):
        self.kind = kind
        if kind == "xgboost":
            self.model = XGBRegressor(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )
        elif kind == "mlp":
            self.model = MLPRegressor(
                hidden_layer_sizes=(32, 16),
                activation="relu",
                alpha=1e-3,
                max_iter=2000,
                random_state=42,
            )
        else:
            raise ValueError(f"Unknown model kind: {kind}")
        self._fitted = False

    def fit(self, training_df: pd.DataFrame) -> None:
        X = training_df[FEATURE_COLUMNS].fillna(0)
        y = training_df[TARGET_COLUMN].fillna(0)
        self.model.fit(X, y)
        self._fitted = True

    def predict(self, players_df: pd.DataFrame) -> np.ndarray:
        if not self._fitted:
            # Cold start (no trained model yet): fall back to a transparent
            # weighted baseline so the app is still useful pre-training.
            return _baseline_score(players_df)
        X = players_df[FEATURE_COLUMNS].fillna(0)
        return self.model.predict(X)

    def feature_importance(self) -> dict[str, float]:
        if not self._fitted or self.kind != "xgboost":
            return {}
        return dict(zip(FEATURE_COLUMNS, self.model.feature_importances_.tolist()))


def _baseline_score(players_df: pd.DataFrame) -> np.ndarray:
    """Transparent weighted-average fallback used until the model has
    real outcome data to train on. Lower ECR/ADP rank and higher
    projected points are better; injury risk penalizes."""
    df = players_df.copy()
    rank_score = 1 / (1 + df["ecr_rank"].fillna(999))
    adp_score = 1 / (1 + df["adp"].fillna(999))
    proj_score = df["projected_ppg"].fillna(0) / (df["projected_ppg"].fillna(0).max() or 1)
    hist_score = df["last_season_ppg"].fillna(0) / (df["last_season_ppg"].fillna(0).max() or 1)
    injury_penalty = 1 - df["injury_risk"].fillna(0)

    score = (
        0.35 * rank_score
        + 0.15 * adp_score
        + 0.30 * proj_score
        + 0.10 * hist_score
    ) * injury_penalty
    return score.to_numpy()
