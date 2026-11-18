"""Tests for ``GET /shopping-list`` (task 1)."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def create_recipe(ingredients: list[str], title: str = "Recipe") -> int:
    """Create a recipe through the API and return its id."""
    response = client.post("/recipes", json={"title": title, "ingredients": ingredients})
    assert response.status_code == 200
    return response.json()["id"]


def get_items(ids: str) -> list[str]:
    """Call the shopping list endpoint for ``ids`` and return its items."""
    response = client.get("/shopping-list", params={"ids": ids})
    assert response.status_code == 200
    return response.json()["items"]


def test_merges_two_recipes_and_dedupes_shared_ingredient():
    first = create_recipe(["flour", "milk", "eggs"])
    second = create_recipe(["flour", "sugar"])

    assert get_items(f"{first},{second}") == ["flour", "milk", "eggs", "sugar"]


def test_first_seen_order_follows_requested_recipe_order():
    first = create_recipe(["banana", "apple"])
    second = create_recipe(["apple", "cherry"])

    assert get_items(f"{first},{second}") == ["banana", "apple", "cherry"]
    assert get_items(f"{second},{first}") == ["apple", "cherry", "banana"]


def test_case_insensitive_dedupe_keeps_first_spelling():
    first = create_recipe(["Flour", "Milk"])
    second = create_recipe(["flour", "MILK", "eggs"])

    assert get_items(f"{first},{second}") == ["Flour", "Milk", "eggs"]


def test_repeated_ids_in_query_count_each_recipe_once():
    first = create_recipe(["flour"])
    second = create_recipe(["milk"])

    assert get_items(f"{first},{first},{second},{first}") == ["flour", "milk"]


def test_single_recipe_keeps_order_and_dedupes_within_recipe():
    recipe = create_recipe(["milk", "flour", "milk"])

    assert get_items(str(recipe)) == ["milk", "flour"]


def test_missing_ids_returns_400():
    response = client.get("/shopping-list")

    assert response.status_code == 400
    assert "ids" in response.json()["detail"]


def test_blank_ids_returns_400():
    for blank in ["", ",", " , ", "   "]:
        response = client.get("/shopping-list", params={"ids": blank})

        assert response.status_code == 400, f"ids={blank!r}"
        assert "ids" in response.json()["detail"]


def test_non_integer_token_returns_400_naming_it():
    recipe = create_recipe(["flour"])

    for bad_token in ["abc", "1.5", "1_0"]:
        response = client.get("/shopping-list", params={"ids": f"{recipe},{bad_token}"})

        assert response.status_code == 400, bad_token
        assert bad_token in response.json()["detail"]


def test_empty_token_between_commas_returns_400():
    recipe = create_recipe(["flour"])

    response = client.get("/shopping-list", params={"ids": f"{recipe},,{recipe}"})

    assert response.status_code == 400
    assert "invalid recipe id" in response.json()["detail"]


def test_unknown_ids_returns_404_naming_each_unknown_id():
    known = create_recipe(["flour"])

    response = client.get("/shopping-list", params={"ids": f"{known},9998,9999"})

    assert response.status_code == 404
    assert response.json()["detail"] == "unknown recipe ids: 9998, 9999"


def test_out_of_range_id_returns_404():
    huge = 2**63

    response = client.get("/shopping-list", params={"ids": str(huge)})

    assert response.status_code == 404
    assert str(huge) in response.json()["detail"]
