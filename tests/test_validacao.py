def test_post_nome_so_com_espacos_retorna_422_e_nao_grava(db_client):
    r = db_client.post("/registros", json={"name": "   ", "height": 4, "weight": 60, "types": []})
    assert r.status_code == 422
    assert db_client.get("/registros").json()["pagination"]["total"] == 0


def test_put_nome_so_com_espacos_retorna_422_e_mantem_registro(db_client):
    db_client.post("/registros", json={"name": "pikachu", "height": 4, "weight": 60, "types": []})
    r = db_client.put("/registros/1", json={"name": "   "})
    assert r.status_code == 422
    assert db_client.get("/registros/1").json()["name"] == "pikachu"


def test_altura_acima_do_limite_retorna_422_e_nao_grava(db_client):
    r = db_client.post("/registros", json={"name": "x", "height": 2_147_483_648, "weight": 1, "types": []})
    assert r.status_code == 422
    assert db_client.get("/registros").json()["pagination"]["total"] == 0


def test_peso_acima_do_limite_no_put_retorna_422(db_client):
    db_client.post("/registros", json={"name": "pikachu", "height": 4, "weight": 60, "types": []})
    r = db_client.put("/registros/1", json={"weight": 2_147_483_648})
    assert r.status_code == 422
    assert db_client.get("/registros/1").json()["weight"] == 60


def test_limite_maximo_do_postgres_e_aceito(db_client):
    r = db_client.post("/registros", json={"name": "x", "height": 2_147_483_647, "weight": 0, "types": []})
    assert r.status_code == 201