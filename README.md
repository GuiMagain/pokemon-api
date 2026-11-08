# API Pokémon

API em FastAPI com duas partes: um CRUD de registros de pokémons em banco relacional (PostgreSQL) e um endpoint que consome a [PokeAPI](https://pokeapi.co/).

**Produção:** https://pokemon-api-aebh.onrender.com/docs

## Stack

| Área | Tecnologia |
|---|---|
| API | FastAPI, Pydantic, httpx |
| Banco relacional | SQLAlchemy 2.0 + PostgreSQL (SQLite em desenvolvimento) |
| Cache | Redis |
| Processamento assíncrono | Celery (broker Redis) |
| Eventos | Kafka (local, via docker-compose) |
| Logs e monitoramento | Logs JSON → Logstash → Elasticsearch → Kibana (local) |
| Containers | Dockerfile, Podman / podman compose |
| Orquestração | Kubernetes (manifesto em `k8s/`, validado sintaticamente) |
| CI/CD | GitHub Actions |
| Deploy | Render |

## Status

| Item | Situação |
|---|---|
| CRUD de registros com PostgreSQL | Testado em produção (Render), incluindo persistência |
| Consumo da PokeAPI (`/pokemons`) | Testado em produção |
| Redis (broker e cache) | Testado em produção |
| Celery (`warm-cache`) | Testado em produção: retorna `202` e enfileira a tarefa |
| Kafka (eventos `pokemon.queried`) | Testado localmente com docker-compose |
| ELK (logs da API no Kibana) | Testado localmente com docker-compose |
| CI/CD com GitHub Actions | Testes e deploy executados com sucesso |
| Kubernetes | Manifesto validado sintaticamente, **não aplicado em cluster** |

## Endpoints

### CRUD de registros (`/registros`)

| Método | Rota | Descrição | Respostas |
|---|---|---|---|
| POST | `/registros` | Cria um registro | 201, 409 (nome duplicado), 422 |
| GET | `/registros?limit=20&offset=0` | Lista paginada | 200 |
| GET | `/registros/{id}` | Busca por id | 200, 404 |
| PUT | `/registros/{id}` | Atualização parcial | 200, 404, 409 |
| DELETE | `/registros/{id}` | Exclui | 204, 404 |

Os nomes são salvos em minúsculas e não podem se repetir.

Exemplo:

```bash
curl -X POST https://pokemon-api-aebh.onrender.com/registros \
  -H "Content-Type: application/json" \
  -d '{"name": "Pikachu", "height": 4, "weight": 60, "types": ["electric"]}'
```

### Consumo da PokeAPI (`/pokemons`)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/pokemons?limit=20&offset=0` | Lista paginada de pokémons vindos da PokeAPI |
| GET | `/pokemons/{id}` | Detalhes de um pokémon (cache no Redis, quando configurado) |
| POST | `/pokemons/warm-cache?start=1&end=151` | Enfileira no Celery o aquecimento do cache. Retorna `202` com `task_id` |

Exemplo de resposta de `GET /pokemons/25`:

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

### Outros

| Rota | Descrição |
|---|---|
| `/health` | Health check |
| `/docs` | Documentação Swagger (OpenAPI) |

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha. O `.env` nunca vai para o Git.

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | Não (padrão: SQLite local) | Conexão com o banco. Aceita `postgres://` e converte automaticamente |
| `REDIS_URL` | Não | Cache dos detalhes da PokeAPI. Sem ela, a API funciona sem cache |
| `CELERY_BROKER_URL` | Só com `warm-cache` | Fila do Celery (Redis) |
| `CACHE_TTL` | Não (padrão: 3600) | Tempo de vida do cache, em segundos |
| `KAFKA_BOOTSTRAP_SERVERS` | Não | Publica eventos `pokemon.queried`. Sem ela, os eventos são ignorados |
| `LOGSTASH_HOST` / `LOGSTASH_PORT` | Não | Envia logs JSON ao Logstash. Sem ela, os logs vão só para o stdout |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Só no docker-compose | Credenciais do container Postgres |

Não há credenciais no código. Os valores padrão são só para desenvolvimento local.

## Rodar localmente

Sem containers, com SQLite:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Acesse http://localhost:8000/docs. O arquivo `pokemon.db` é criado automaticamente na primeira execução.

## Testes

```bash
pytest --cov=app --cov-report=term-missing
```

Os testes não precisam de internet, Redis, Kafka nem Postgres. O CRUD usa SQLite em memória, e a PokeAPI é simulada com `httpx.MockTransport`. O CI exige cobertura mínima de 70%.

## Containers com Podman

Imagem sozinha:

```bash
podman build -t pokemon-api .
podman run -p 8000:8000 -e DATABASE_URL=sqlite:///./pokemon.db pokemon-api
```

Stack completa (API, worker do Celery, Postgres, Redis, Kafka, Elasticsearch, Logstash e Kibana):

```bash
cp .env.example .env     # preencha as senhas
podman compose up -d
```

Serviços após subir:

- API: http://localhost:8000/docs
- Kibana: http://localhost:5601
- Elasticsearch: http://localhost:9200

No macOS ou Windows, rode `podman machine start` antes.

No Fedora, o Podman usa nomes completos de imagem (`docker.io/...`). O volume do Logstash usa a opção `:z` para o SELinux permitir a leitura da pasta `logstash/pipeline`.

### Visualizando os logs no Kibana

1. Gere algumas requisições na API.
2. Acesse http://localhost:5601.
3. Em **Stack Management → Data Views → Create data view**, crie o padrão `pokemon-api-*` com o campo de tempo `@timestamp`.
4. Abra o **Discover** para ver as requisições registradas (método, rota, status e tempo de resposta).

## Deploy no Render

O deploy usa três serviços gratuitos:

1. **PostgreSQL** (`pokemon-db`): copie a *Internal Database URL* e use como `DATABASE_URL`.
2. **Key Value** (Redis): copie a *Internal Connection String* e use como `REDIS_URL` e `CELERY_BROKER_URL`.
3. **Web Service** (`pokemon-api`, runtime Docker): todas as variáveis acima, mais `CACHE_TTL=3600`. Health check em `/health`. Auto-deploy desligado, porque o deploy é feito pelo pipeline.

O Web Service roda a API e o worker do Celery no mesmo container, pelo script `start.sh`. O worker separado do Render é pago, então essa foi a alternativa gratuita.

Kafka e ELK não rodam no Render, porque não há versões gratuitas. Eles funcionam localmente pelo `docker-compose`.

## CI/CD

Workflow em `.github/workflows/ci.yml`, acionado em push e pull request para `main`:

1. **test:** instala as dependências e roda os testes com cobertura mínima de 70%.
2. **build-and-deploy** (só em push para `main`, depois dos testes): constrói a imagem, publica no GitHub Container Registry e chama o deploy hook do Render.

Secret necessário: `RENDER_DEPLOY_HOOK_URL` (em Settings → Secrets and variables → Actions).

## Kubernetes

O manifesto `k8s/pokemon-api.yaml` contém 6 recursos: ConfigMap, Deployments da API, do worker e do Redis, e Services da API e do Redis.

Ele foi **validado sintaticamente**, mas **não foi aplicado em um cluster**. Não consegui subir um cluster local (kind ou minikube) neste ambiente.

O Render não executa manifestos Kubernetes. O deploy de produção usa o Dockerfile diretamente, e o manifesto serve como referência de orquestração.

## Decisões técnicas

- **Rotas separadas:** o CRUD fica em `/registros` e a leitura da PokeAPI em `/pokemons`, para não colidirem.
- **Sem result backend no Celery:** a API só envia tarefas e não lê os resultados. Por isso `CELERY_RESULT_BACKEND` não é usado.
- **Worker no mesmo container:** alternativa gratuita ao Background Worker do Render. Em produção, o ideal é separar a API e o worker em serviços diferentes.
- **Falhas de Redis e Kafka não derrubam a API:** cache e eventos são opcionais. A falha é registrada no log e a requisição segue.
- **Configuração por variável de ambiente:** nenhuma credencial fica no código ou no repositório.
- **Logs de requisição:** um middleware registra método, rota, status e tempo de cada chamada, que é o que chega ao Kibana.

## Limitações conhecidas

- O manifesto do Kubernetes ainda não inclui o Postgres nem a variável `DATABASE_URL`, e não foi aplicado em cluster.
- Kafka e ELK foram testados apenas localmente, não em produção.
- O Postgres gratuito do Render expira após 30 dias.
- Os testes automatizados usam SQLite em memória, não o Postgres. A persistência em Postgres foi verificada manualmente no Render.
