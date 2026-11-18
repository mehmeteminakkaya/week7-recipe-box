"""Tests for GET /recipes/{id}/scaled (task 3) — generator draft v2."""

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _recipe(ingredients: list[str]) -> int:
    response = client.post(
        "/recipes",
        json={"title": "Pancakes", "ingredients": ingredients, "tags": ["breakfast"]},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_scales_leading_quantities():
    recipe_id = _recipe(["200 g flour", "3 eggs"])

    body = client.get(f"/recipes/{recipe_id}/scaled?factor=2").json()

    assert body["ingredients"] == ["400 g flour", "6 eggs"]


def test_factor_defaults_to_two():
    recipe_id = _recipe(["200 g flour"])

    assert client.get(f"/recipes/{recipe_id}/scaled").json()["ingredients"] == ["400 g flour"]


def test_factor_one_is_an_identity():
    recipe_id = _recipe(["1000000 g water", "123.4567 g yeast"])

    body = client.get(f"/recipes/{recipe_id}/scaled?factor=1").json()

    # No scientific notation ("1e+06") and no rounding ("123.457").
    assert body["ingredients"] == ["1000000 g water", "123.4567 g yeast"]


def test_large_integers_keep_full_precision():
    recipe_id = _recipe(["1234567 g rice"])

    body = client.get(f"/recipes/{recipe_id}/scaled?factor=2").json()

    assert body["ingredients"] == ["2469134 g rice"]


def test_decimal_quantity_scales_exactly():
    recipe_id = _recipe(["0.1 kg sugar"])

    body = client.get(f"/recipes/{recipe_id}/scaled?factor=3").json()

    assert body["ingredients"] == ["0.3 kg sugar"]


def test_ingredients_without_quantity_are_unchanged():
    recipe_id = _recipe(["salt to taste"])

    body = client.get(f"/recipes/{recipe_id}/scaled?factor=2").json()

    assert body["ingredients"] == ["salt to taste"]


@pytest.mark.parametrize(
    "ingredient",
    [
        "1/2 cup milk",  # fraction: not half-parsed
        "2,5 kg salt",  # comma decimal: not misread as "2"
        "200g flour",  # no separating space, so not a standalone token
    ],
)
def test_non_standalone_quantities_are_left_alone(ingredient):
    recipe_id = _recipe([ingredient])

    body = client.get(f"/recipes/{recipe_id}/scaled?factor=2").json()

    assert body["ingredients"] == [ingredient]


@pytest.mark.parametrize("factor", ["0", "-1", "101", "inf", "nan"])
def test_out_of_range_factor_is_rejected(factor):
    recipe_id = _recipe(["200 g flour"])

    assert client.get(f"/recipes/{recipe_id}/scaled?factor={factor}").status_code == 422


@pytest.mark.parametrize("factor", ["abc", ""])
def test_unparseable_factor_is_rejected_with_detail(factor):
    recipe_id = _recipe(["200 g flour"])

    response = client.get(f"/recipes/{recipe_id}/scaled?factor={factor}")

    assert response.status_code == 422
    assert "detail" in response.json()


def test_unknown_recipe_is_404_with_detail():
    response = client.get("/recipes/99999/scaled?factor=2")

    assert response.status_code == 404
    assert response.json() == {"detail": "unknown recipe"}


def test_response_shape_matches_get_recipe():
    recipe_id = _recipe(["200 g flour"])
    original = client.get(f"/recipes/{recipe_id}").json()

    scaled = client.get(f"/recipes/{recipe_id}/scaled?factor=2").json()

    assert set(scaled) == set(original)
    assert scaled["id"] == original["id"]
    assert scaled["title"] == original["title"]
    assert scaled["tags"] == original["tags"]


def test_scaling_does_not_persist():
    recipe_id = _recipe(["200 g flour"])

    client.get(f"/recipes/{recipe_id}/scaled?factor=2")

    assert client.get(f"/recipes/{recipe_id}").json()["ingredients"] == ["200 g flour"]
