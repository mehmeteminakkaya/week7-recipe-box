"""Tests for GET /recipes/{id}/scaled (task 3) — generator draft v1."""

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


def test_ingredients_without_quantity_are_unchanged():
    recipe_id = _recipe(["salt to taste"])

    body = client.get(f"/recipes/{recipe_id}/scaled?factor=2").json()

    assert body["ingredients"] == ["salt to taste"]


def test_unknown_recipe_is_404():
    assert client.get("/recipes/99999/scaled?factor=2").status_code == 404
