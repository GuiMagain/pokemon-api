from app.services.pokeapi import _to_detail


def test_to_detail_extrai_os_campos_pedidos(raw_pikachu):
    detail = _to_detail(raw_pikachu)
    assert detail.name == "pikachu"
    assert detail.id == 25
    assert detail.height == 4
    assert detail.weight == 60
    assert detail.types == ["electric"]
    assert detail.sprites.front_default.endswith("25.png")
    assert detail.sprites.back_default is not None
