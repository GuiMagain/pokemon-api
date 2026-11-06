# API Pokémon

API em FastAPI que consome a [PokeAPI](https://pokeapi.co/) e expõe Pokémons paginados.

## Stack

- FastAPI + httpx (consumo assíncrono da PokeAPI)
- Redis (cache dos detalhes)
- Celery + Redis como broker (aquecimento de cache em background)
- Kafka (eventos de consulta)
- Logs em JSON enviados ao Logstash → Elasticsearch → Kibana (ELK)
- Podman / podman compose, Kubernetes, GitHub Actions, Render

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/pokemons?limit=20&offset=0` | Lista paginada |
| GET | `/pokemons/{id}` | Detalhes de um Pokémon |
| POST | `/pokemons/warm-cache?start=1&end=151` | Enfileira aquecimento do cache (Celery) |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

Exemplo: `GET /pokemons/25`

```json
{
  "name": "pikachu",
  "id": 25,
  "height": 4,
  "weight": 60,
  "types": ["electric"],
  "sprites": {
    "front_default": "https://raw.githubusercontent.com/...",
    "back_default": "https://raw.githubusercontent.com/..."
  }
}
```

## Rodar localmente (sem containers)

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Acesse http://localhost:8000/docs

## Testes

```bash
pytest --cov=app --cov-report=term-missing
```

## Containers com Podman

```bash
podman build -t pokemon-api .
podman run -p 8000:8000 pokemon-api

# stack completa (API, worker, Redis, Kafka, ELK)
podman compose up -d
```

No macOS/Windows, rode `podman machine start` antes.

## Kubernetes

Troque `SEU_USUARIO` em `k8s/pokemon-api.yaml` pelo seu usuário do GitHub, publique a imagem e aplique:

```bash
kubectl apply -f k8s/pokemon-api.yaml
kubectl get svc pokemon-api
```

Para cluster local (kind/minikube), carregue a imagem no cluster antes de aplicar.

## CI/CD (GitHub Actions)

O workflow `.github/workflows/ci.yml`:

1. roda os testes com cobertura mínima de 70%;
2. em push para `main`, constrói a imagem, publica no GHCR e chama o deploy hook do Render.

Configure em **Settings → Secrets and variables → Actions**: `RENDER_DEPLOY_HOOK_URL`.

## Deploy no Render

1. No Render, crie um **Web Service** a partir do repositório (ou use o `render.yaml` como Blueprint).
2. Em *Environment*, defina `REDIS_URL` e `KAFKA_BOOTSTRAP_SERVERS` se tiver esses serviços (são opcionais).
3. Copie o **Deploy Hook** do serviço e salve como secret `RENDER_DEPLOY_HOOK_URL`.
4. Desative o auto-deploy se quiser que só o pipeline faça o deploy.
