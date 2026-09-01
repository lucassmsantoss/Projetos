"""Merges Sleeper catalog + FantasyPros projections/news + historical stats
into a single list of PlayerProfile records ready for the ranking model.
"""
from __future__ import annotations

from app.clients.fantasypros_client import FantasyProsClient
from app.clients.historical_stats_client import load_player_id_map, load_seasonal_fantasy_stats
from app.clients.sleeper_client import SleeperClient
from app.models.player import InjuryInfo, PlayerProfile, Projection, SeasonStats

RELEVANT_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF"}


def build_player_universe(season: int, fantasypros_api_key: str) -> list[PlayerProfile]:
    sleeper = SleeperClient()
    fp = FantasyProsClient(api_key=fantasypros_api_key)

    try:
        all_players = sleeper.get_all_players()
        id_map = load_player_id_map()
        gsis_by_sleeper = {
            row["sleeper_id"]: row["gsis_id"]
            for row in id_map.to_dict("records")
            if row.get("sleeper_id")
        }

        last_season_stats = load_seasonal_fantasy_stats(season - 1).set_index("gsis_id")

        projections_by_position: dict[str, dict] = {}
        for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            try:
                projections_by_position[pos] = fp.get_projections(season, pos)
            except Exception:
                projections_by_position[pos] = {}

        profiles: list[PlayerProfile] = []
        for pid, info in all_players.items():
            position = info.get("position")
            if position not in RELEVANT_POSITIONS:
                continue
            if info.get("status") == "Inactive" and not info.get("team"):
                continue

            full_name = info.get("full_name") or f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
            if not full_name:
                continue

            stats = None
            gsis_id = gsis_by_sleeper.get(pid)
            if gsis_id is not None and gsis_id in last_season_stats.index:
                row = last_season_stats.loc[gsis_id]
                stats = SeasonStats(
                    season=season - 1,
                    games_played=int(row.get("games_played") or 0),
                    fantasy_points_ppr=float(row.get("fantasy_points_ppr") or 0),
                    fantasy_points_per_game_ppr=float(row.get("fantasy_points_per_game_ppr") or 0),
                    targets=row.get("targets"),
                    receptions=row.get("receptions"),
                    rush_attempts=row.get("rushing_att"),
                    pass_attempts=row.get("attempts"),
                )

            projection = _match_projection(projections_by_position.get(position, {}), full_name, season)

            profiles.append(
                PlayerProfile(
                    sleeper_id=pid,
                    full_name=full_name,
                    position=position,
                    team=info.get("team"),
                    age=info.get("age"),
                    years_exp=info.get("years_exp"),
                    status=info.get("status"),
                    injury=InjuryInfo(
                        status=info.get("injury_status"),
                        body_part=info.get("injury_body_part"),
                        note=info.get("injury_notes"),
                    ),
                    last_season_stats=stats,
                    projection=projection,
                )
            )
        return profiles
    finally:
        sleeper.close()
        fp.close()


def _match_projection(fp_payload: dict, full_name: str, season: int) -> Projection | None:
    """FantasyPros responses key players by their own IDs; match by name as a
    pragmatic default. Swap for an ID crosswalk once the live payload shape
    is confirmed against your API key."""
    players = fp_payload.get("players", []) if isinstance(fp_payload, dict) else []
    for p in players:
        if p.get("name", "").strip().lower() == full_name.strip().lower():
            stats = p.get("stats", {})
            return Projection(
                season=season,
                source="fantasypros",
                projected_points_ppr=float(stats.get("points", 0) or 0),
                ecr_rank=p.get("rank_ecr"),
                ecr_position_rank=p.get("pos_rank"),
                adp=p.get("adp"),
            )
    return None
