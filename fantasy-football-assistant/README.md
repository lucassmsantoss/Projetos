# Fantasy Football Draft Assistant

App para ajudar em decisões de draft no fantasy football da NFL (Sleeper),
combinando:
- Catálogo de jogadores e estado da liga (rosters, drafts) via **Sleeper API**.
- Projeções, rankings de consenso e notícias/lesões via **FantasyPros API**.
- Estatísticas históricas de temporadas passadas via **nfl_data_py**.
- Um modelo de valor (gradient boosting, `XGBoost`) treinado para prever o
  desempenho futuro do jogador, combinado com a sua necessidade de roster e
  a escassez posicional entre os adversários na liga, para recomendar o
  próximo pick.

## Por que gradient boosting em vez de rede neural pura

Dados de draft são tabulares, com poucas centenas de jogadores relevantes por
temporada e features heterogêneas (ranks, taxas, categorias). Boosted trees
lidam melhor com esse formato com menos dados/tuning que uma rede neural, e
expõem `feature_importances_` — importante para explicar *por que* um
jogador foi recomendado. Uma MLP (rede neural) está disponível como
alternativa em `backend/app/ml/value_model.py` (`PlayerValueModel(kind="mlp")`)
para comparação, caso você prefira usar rede neural mesmo.

## Estrutura

```
fantasy-football-assistant/
  backend/    FastAPI + pipeline de dados + modelo de ML
  frontend/   React (Vite + TS) — dashboard de draft
```

## Setup local

### Backend

```bash
cd fantasy-football-assistant/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha FANTASYPROS_API_KEY e SLEEPER_LEAGUE_ID
uvicorn app.main:app --reload
```

Endpoints principais:
- `GET /health`
- `GET /draft/league-state` — rosters e usuários da liga configurada.
- `GET /draft/recommendations?my_user_id=<seu_sleeper_user_id>` — top picks
  recomendados, considerando seu roster e o dos adversários.

> Seu `user_id` do Sleeper (diferente do `league_id`) pode ser obtido em
> `https://api.sleeper.app/v1/user/<seu_username>`.

### Frontend

```bash
cd fantasy-football-assistant/frontend
npm install
cp .env.example .env   # ajuste VITE_API_BASE se o backend não estiver em localhost:8000
npm run dev
```

## Treinando o modelo de valor

Por padrão o modelo roda em modo "cold start": um score transparente
ponderado (ECR, ADP, projeção, histórico) até que seja treinado com dados
reais. Para treinar com múltiplas temporadas passadas:

```python
from app.ml.training import build_training_set
from app.ml.value_model import PlayerValueModel

df = build_training_set(seasons=[2022, 2023, 2024, 2025])
model = PlayerValueModel(kind="xgboost")
model.fit(df)
```
(Persistência do modelo treinado — ex: `joblib.dump` — ainda não está
integrada ao endpoint; é o próximo passo natural do pipeline.)

## Status / próximos passos

- [x] Modelo de dados unificado do jogador (Sleeper + FantasyPros + histórico)
- [x] Cliente Sleeper (players, league, rosters, drafts)
- [x] Cliente FantasyPros (projeções, rankings, news) — **endpoints não
      testados contra a API real neste ambiente** (rede bloqueada no sandbox
      de desenvolvimento); validar o shape da resposta com sua chave antes
      do primeiro uso real e ajustar `_match_projection`/parsing se necessário.
- [x] Cálculo de necessidade do meu roster e escassez posicional na liga
- [x] Recomendador combinando valor + necessidade + escassez
- [x] Dashboard React consumindo a API
- [ ] Persistir modelo treinado e re-treinar periodicamente
- [ ] Cache/DB para não bater nas APIs a cada request (Sleeper pede cache
      diário do catálogo de players)
- [ ] Deploy (backend: Render/Railway; frontend: Vercel)
- [ ] Autenticação simples (é um app pessoal, mas se for exposto publicamente
      precisa de proteção básica)
- [ ] Suporte a waiver wire / trocas durante a temporada (fase 2)
