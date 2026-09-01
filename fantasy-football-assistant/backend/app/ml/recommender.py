"""Final draft-pick recommender: combines the player value model's score
with *your* roster need and league-wide positional scarcity, so a
strong player at a position you already have covered ranks below a
merely-good player at a position you (and the market) are neglecting.
"""
from __future__ import annotations

import pandas as pd

from app.ml.value_model import PlayerValueModel
from app.models.player import PlayerProfile
from app.services.roster_service import LeagueDraftState, compute_my_need, compute_position_scarcity

NEED_WEIGHT = 0.35
SCARCITY_WEIGHT = 0.15
VALUE_WEIGHT = 0.50


def recommend_picks(
    players: list[PlayerProfile],
    league_state: LeagueDraftState,
    value_model: PlayerValueModel,
    top_n: int = 15,
) -> list[dict]:
    my_team = next(t for t in league_state.teams if t.is_me)
    my_need = compute_my_need(my_team)
    scarcity = compute_position_scarcity(league_state)

    drafted_ids = {pid for t in league_state.teams for pid in t.player_ids}
    available = [p for p in players if p.sleeper_id not in drafted_ids]

    df = pd.DataFrame([p.to_feature_dict() for p in available])
    if df.empty:
        return []

    df["value_score"] = value_model.predict(df)
    # normalize to 0-1 within the current available pool
    max_val = df["value_score"].max() or 1
    df["value_score_norm"] = df["value_score"] / max_val

    df["need_score"] = df["position"].map(my_need).fillna(0.0)
    # "market scarcity opportunity": lower means fewer opponents have this
    # position yet -> could be safe to wait; we invert to reward positions
    # where competitors are aggressively drafting (signals real value/run).
    df["scarcity_score"] = df["position"].map(scarcity).fillna(0.0)

    df["final_score"] = (
        VALUE_WEIGHT * df["value_score_norm"]
        + NEED_WEIGHT * df["need_score"]
        + SCARCITY_WEIGHT * df["scarcity_score"]
    )

    df = df.sort_values("final_score", ascending=False).head(top_n)

    by_id = {p.sleeper_id: p for p in available}
    results = []
    for _, row in df.iterrows():
        player = by_id[row["sleeper_id"]]
        results.append(
            {
                "sleeper_id": player.sleeper_id,
                "name": player.full_name,
                "position": player.position,
                "team": player.team,
                "final_score": round(float(row["final_score"]), 4),
                "value_score": round(float(row["value_score_norm"]), 4),
                "my_need_score": round(float(row["need_score"]), 4),
                "league_scarcity_score": round(float(row["scarcity_score"]), 4),
                "reasoning": _explain(row, my_need),
            }
        )
    return results


def _explain(row: pd.Series, my_need: dict[str, float]) -> str:
    pos = row["position"]
    need = my_need.get(pos, 0)
    if need < 0.2:
        need_note = f"você já está bem coberto em {pos}, prioridade baixa por necessidade"
    elif need < 0.6:
        need_note = f"você tem cobertura parcial em {pos}"
    else:
        need_note = f"você ainda precisa de titular em {pos}"

    if row["scarcity_score"] > 0.7:
        market_note = "a maioria dos adversários já tem essa posição — a janela de valor pode estar fechando"
    elif row["scarcity_score"] < 0.3:
        market_note = "poucos adversários pegaram essa posição ainda — pode dar pra esperar mais rodadas"
    else:
        market_note = "mercado dividido nessa posição entre os adversários"

    return f"{need_note}; {market_note}."
