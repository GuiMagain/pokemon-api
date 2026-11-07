PIKACHU = {"name": "Pikachu", "height": 4, "weight": 60, "types": ["electric"]}


def test_criar_retorna_201_e_normaliza_nome(db_client):
    r = db_client.post("/registros", json=PIKACHU)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["name"] == "pikachu"
    assert body["types"] == ["electric"]


def test_criar_nome_duplicado_retorna_409(db_client):
    db_client.post("/registros", json=PIKACHU)
    assert db_client.post("/registros", json=PIKACHU).status_code == 409


def test_criar_com_altura_negativa_retorna_422(db_client):
    assert db_client.post("/registros", json={**PIKACHU, "height": -1}).status_code == 422


def test_criar_sem_nome_retorna_422(db_client):
    assert db_client.post("/registros", json={**PIKACHU, "name": ""}).status_code == 422


def test_listar_com_paginacao(db_client):
    for i in range(3):
        db_client.post("/registros", json={**PIKACHU, "name": f"poke{i}"})

    body = db_client.get("/registros", params={"limit": 2, "offset": 0}).json()
    assert len(body["data"]) == 2
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["next"] == "/registros?limit=2&offset=2"
    assert body["pagination"]["previous"] is None


def test_buscar_por_id(db_client):
    db_client.post("/registros", json=PIKACHU)
    assert db_client.get("/registros/1").json()["name"] == "pikachu"


def test_buscar_inexistente_retorna_404(db_client):
    assert db_client.get("/registros/999").status_code == 404


def test_atualizar_parcialmente_mantem_campos_nao_enviados(db_client):
    db_client.post("/registros", json=PIKACHU)
    r = db_client.put("/registros/1", json={"weight": 70})
    assert r.status_code == 200
    assert r.json()["weight"] == 70
    assert r.json()["name"] == "pikachu"


def test_atualizar_campo_obrigatorio_com_null_e_ignorado(db_client):
    db_client.post("/registros", json=PIKACHU)
    r = db_client.put("/registros/1", json={"name": None})
    assert r.status_code == 200
    assert r.json()["name"] == "pikachu"


def test_atualizar_inexistente_retorna_404(db_client):
    assert db_client.put("/registros/999", json={"weight": 1}).status_code == 404


def test_excluir_e_depois_404(db_client):
    db_client.post("/registros", json=PIKACHU)
    assert db_client.delete("/registros/1").status_code == 204
    assert db_client.get("/registros/1").status_code == 404


def test_excluir_inexistente_retorna_404(db_client):
    assert db_client.delete("/registros/999").status_code == 404
