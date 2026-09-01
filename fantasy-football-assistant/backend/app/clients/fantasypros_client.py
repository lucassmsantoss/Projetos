"""Client for the FantasyPros API (https://www.fantasypros.com/api-data/).

NOTE: this sandbox environment blocks outbound calls to fantasypros.com,
so these endpoint paths follow FantasyPros' published v2 API structure
but have NOT been exercised against a live response here. Verify against
your API key's docs (linked from the FantasyPros API dashboard) on first
run and adjust field names if their response shape differs.
"""
from __future__ import annotations

import httpx

BASE_URL = "https://api.fantasypros.com/public/v2/json"

POSITION_MAP = {
    "QB": "QB",
    "RB": "RB",
    "WR": "WR",
    "TE": "TE",
    "K": "K",
    "DEF": "DST",
}


class FantasyProsClient:
    def __init__(self, api_key: str, timeout: float = 15.0):
        self._client = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"x-api-key": api_key},
        )

    def get_projections(self, season: int, position: str, week: int = 0, scoring: str = "PPR") -> dict:
        """week=0 means season-long (draft) projections."""
        fp_pos = POSITION_MAP.get(position, position)
        resp = self._client.get(
            f"/nfl/{season}/projections",
            params={"week": week, "position": fp_pos, "scoring": scoring},
        )
        resp.raise_for_status()
        return resp.json()

    def get_consensus_rankings(self, season: int, position: str, week: int = 0, scoring: str = "PPR") -> dict:
        fp_pos = POSITION_MAP.get(position, position)
        resp = self._client.get(
            f"/nfl/{season}/consensus-rankings",
            params={"week": week, "position": fp_pos, "type": "ST", "scoring": scoring},
        )
        resp.raise_for_status()
        return resp.json()

    def get_player_news(self, season: int) -> dict:
        resp = self._client.get(f"/nfl/{season}/news")
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()
