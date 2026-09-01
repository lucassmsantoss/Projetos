"""Reads league state from Sleeper: your roster, everyone else's roster,
and derives positional need/scarcity signals for the draft recommender.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.clients.sleeper_client import SleeperClient

STARTER_SLOTS_DEFAULT = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1}


class TeamRosterState(BaseModel):
    roster_id: int
    owner_display_name: str
    is_me: bool
    player_ids: list[str]
    position_counts: dict[str, int]


class LeagueDraftState(BaseModel):
    league_id: str
    total_teams: int
    my_roster_id: int
    teams: list[TeamRosterState]
    league_position_counts: dict[str, int]  # aggregate across all teams


def get_league_draft_state(league_id: str, my_user_id: str, sleeper_players: dict) -> LeagueDraftState:
    client = SleeperClient()
    try:
        rosters = client.get_rosters(league_id)
        users = client.get_users(league_id)
    finally:
        client.close()

    user_id_to_display = {u["user_id"]: u.get("display_name", u["user_id"]) for u in users}

    teams: list[TeamRosterState] = []
    league_position_counts: dict[str, int] = {}
    my_roster_id = -1

    for roster in rosters:
        player_ids = roster.get("players") or []
        position_counts: dict[str, int] = {}
        for pid in player_ids:
            pos = sleeper_players.get(pid, {}).get("position")
            if not pos:
                continue
            position_counts[pos] = position_counts.get(pos, 0) + 1
            league_position_counts[pos] = league_position_counts.get(pos, 0) + 1

        owner_id = roster.get("owner_id")
        is_me = owner_id == my_user_id
        if is_me:
            my_roster_id = roster["roster_id"]

        teams.append(
            TeamRosterState(
                roster_id=roster["roster_id"],
                owner_display_name=user_id_to_display.get(owner_id, "Unknown"),
                is_me=is_me,
                player_ids=player_ids,
                position_counts=position_counts,
            )
        )

    return LeagueDraftState(
        league_id=league_id,
        total_teams=len(rosters),
        my_roster_id=my_roster_id,
        teams=teams,
        league_position_counts=league_position_counts,
    )


def compute_position_scarcity(state: LeagueDraftState) -> dict[str, float]:
    """Fraction of teams (excluding me) that already have >=1 player at a
    position. High value = position is being drafted heavily by others =
    less urgent for me to reach for it right now; low value = position is
    being neglected = could be a market inefficiency to exploit, OR simply
    early in the draft. The recommender combines this with my own need.
    """
    other_teams = [t for t in state.teams if not t.is_me]
    if not other_teams:
        return {}
    scarcity: dict[str, float] = {}
    for pos in STARTER_SLOTS_DEFAULT:
        teams_with_pos = sum(1 for t in other_teams if t.position_counts.get(pos, 0) >= 1)
        scarcity[pos] = teams_with_pos / len(other_teams)
    return scarcity


def compute_my_need(my_team: TeamRosterState) -> dict[str, float]:
    """1.0 = still need starters at this position, 0.0 = fully covered
    (or better), scaled down as bench depth is filled."""
    need: dict[str, float] = {}
    for pos, starter_slots in STARTER_SLOTS_DEFAULT.items():
        if pos == "FLEX":
            continue
        have = my_team.position_counts.get(pos, 0)
        need[pos] = max(0.0, min(1.0, 1.0 - (have / starter_slots)))
    return need
