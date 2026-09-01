"""Client for the public Sleeper API (https://docs.sleeper.com).

All endpoints are unauthenticated GET requests. Sleeper asks integrators
to cache /players/nfl locally and refresh at most once a day, since it
returns the full ~5-10MB player catalog.
"""
from __future__ import annotations

import httpx

BASE_URL = "https://api.sleeper.app/v1"


class SleeperClient:
    def __init__(self, timeout: float = 15.0):
        self._client = httpx.Client(base_url=BASE_URL, timeout=timeout)

    def get_all_players(self) -> dict:
        """Full NFL player catalog, keyed by sleeper player_id. Cache this."""
        resp = self._client.get("/players/nfl")
        resp.raise_for_status()
        return resp.json()

    def get_league(self, league_id: str) -> dict:
        resp = self._client.get(f"/league/{league_id}")
        resp.raise_for_status()
        return resp.json()

    def get_rosters(self, league_id: str) -> list[dict]:
        resp = self._client.get(f"/league/{league_id}/rosters")
        resp.raise_for_status()
        return resp.json()

    def get_users(self, league_id: str) -> list[dict]:
        resp = self._client.get(f"/league/{league_id}/users")
        resp.raise_for_status()
        return resp.json()

    def get_drafts_for_league(self, league_id: str) -> list[dict]:
        resp = self._client.get(f"/league/{league_id}/drafts")
        resp.raise_for_status()
        return resp.json()

    def get_draft_picks(self, draft_id: str) -> list[dict]:
        resp = self._client.get(f"/draft/{draft_id}/picks")
        resp.raise_for_status()
        return resp.json()

    def get_trending_players(self, sport: str = "nfl", pick_type: str = "add", hours: int = 24, limit: int = 25) -> list[dict]:
        resp = self._client.get(
            f"/players/{sport}/trending/{pick_type}",
            params={"lookback_hours": hours, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()
