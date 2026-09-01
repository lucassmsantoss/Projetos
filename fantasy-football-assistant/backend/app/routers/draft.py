from fastapi import APIRouter, HTTPException

from app.clients.sleeper_client import SleeperClient
from app.config import settings
from app.ml.value_model import PlayerValueModel
from app.ml.recommender import recommend_picks
from app.services.player_data_service import build_player_universe
from app.services.roster_service import get_league_draft_state

router = APIRouter(prefix="/draft", tags=["draft"])

_value_model = PlayerValueModel(kind="xgboost")  # cold-start baseline until trained


@router.get("/recommendations")
def get_recommendations(my_user_id: str, top_n: int = 15):
    sleeper = SleeperClient()
    try:
        sleeper_players = sleeper.get_all_players()
    finally:
        sleeper.close()

    league_state = get_league_draft_state(
        league_id=settings.sleeper_league_id,
        my_user_id=my_user_id,
        sleeper_players=sleeper_players,
    )
    if league_state.my_roster_id == -1:
        raise HTTPException(status_code=404, detail="my_user_id não encontrado nesta liga")

    players = build_player_universe(settings.nfl_season, settings.fantasypros_api_key)
    recommendations = recommend_picks(players, league_state, _value_model, top_n=top_n)
    return {
        "league_id": settings.sleeper_league_id,
        "season": settings.nfl_season,
        "recommendations": recommendations,
    }


@router.get("/league-state")
def get_league_state():
    sleeper = SleeperClient()
    try:
        sleeper_players = sleeper.get_all_players()
        rosters = sleeper.get_rosters(settings.sleeper_league_id)
        users = sleeper.get_users(settings.sleeper_league_id)
    finally:
        sleeper.close()
    return {"rosters": rosters, "users": users}
