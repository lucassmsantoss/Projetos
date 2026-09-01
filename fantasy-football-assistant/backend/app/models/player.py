from typing import Optional
from pydantic import BaseModel


class InjuryInfo(BaseModel):
    status: Optional[str] = None  # Healthy, Questionable, Doubtful, Out, IR, PUP
    body_part: Optional[str] = None
    note: Optional[str] = None
    practice_participation: Optional[str] = None


class SeasonStats(BaseModel):
    season: int
    games_played: int = 0
    fantasy_points_ppr: float = 0.0
    fantasy_points_per_game_ppr: float = 0.0
    targets: Optional[float] = None
    receptions: Optional[float] = None
    rush_attempts: Optional[float] = None
    pass_attempts: Optional[float] = None
    touchdowns: Optional[float] = None
    yards: Optional[float] = None
    snap_share: Optional[float] = None


class Projection(BaseModel):
    season: int
    source: str  # "fantasypros"
    projected_points_ppr: float
    projected_points_per_game_ppr: Optional[float] = None
    ecr_rank: Optional[int] = None  # expert consensus rank overall
    ecr_position_rank: Optional[int] = None
    adp: Optional[float] = None  # average draft position


class PlayerProfile(BaseModel):
    """Unified player record merging Sleeper + FantasyPros + historical stats."""

    sleeper_id: str
    full_name: str
    position: str  # QB, RB, WR, TE, K, DEF
    team: Optional[str] = None
    age: Optional[int] = None
    years_exp: Optional[int] = None
    status: Optional[str] = None  # Active, Inactive, etc (Sleeper roster status)

    injury: InjuryInfo = InjuryInfo()
    last_season_stats: Optional[SeasonStats] = None
    projection: Optional[Projection] = None

    news_headlines: list[str] = []

    def to_feature_dict(self) -> dict:
        """Flatten into scalar features for the ranking model."""
        stats = self.last_season_stats
        proj = self.projection
        return {
            "sleeper_id": self.sleeper_id,
            "position": self.position,
            "age": self.age or 0,
            "years_exp": self.years_exp or 0,
            "injury_risk": _injury_risk_score(self.injury.status),
            "last_season_ppg": stats.fantasy_points_per_game_ppr if stats else 0.0,
            "last_season_games": stats.games_played if stats else 0,
            "projected_ppg": proj.projected_points_per_game_ppr if proj and proj.projected_points_per_game_ppr else 0.0,
            "projected_points": proj.projected_points_ppr if proj else 0.0,
            "ecr_rank": proj.ecr_rank if proj and proj.ecr_rank else 999,
            "ecr_position_rank": proj.ecr_position_rank if proj and proj.ecr_position_rank else 999,
            "adp": proj.adp if proj and proj.adp else 999.0,
        }


def _injury_risk_score(status: Optional[str]) -> float:
    """0 = no risk, 1 = maximum risk (won't play)."""
    mapping = {
        None: 0.0,
        "Healthy": 0.0,
        "Probable": 0.1,
        "Questionable": 0.35,
        "Doubtful": 0.7,
        "Out": 0.95,
        "IR": 1.0,
        "PUP": 1.0,
        "Suspended": 1.0,
    }
    return mapping.get(status, 0.2)
