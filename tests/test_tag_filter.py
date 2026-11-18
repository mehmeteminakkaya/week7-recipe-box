"""Tests for the ``GET /recipes?tag=`` filter (task 2 in docs/TASKS.md)."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _create(title: str, tags: list[str], ingredients: list[str] | None = None) -> int:
    r = client.post(
        "/recipes",
        json={
            "title": title,
            "ingredients": ingredients if ingredients is not None else ["water"],
            "tags": tags,
        },
    )
    assert r.status_code == 200
    return r.json()["id"]


def test_tag_filter_returns_only_recipes_with_that_tag():
    breakfast_id = _create("Pancakes", ["breakfast", "sweet"])
    _create("Boxing Day Stew", ["dinner"], ingredients=["beef"])

    r = client.get("/recipes", params={"tag": "breakfast"})

    assert r.status_code == 200
    recipes = r.json()
    assert len(recipes) == 1
    assert recipes[0]["id"] == breakfast_id
    assert recipes[0]["title"] == "Pancakes"
    assert recipes[0]["tags"] == ["breakfast", "sweet"]


def test_tag_filter_matches_case_insensitively():
    breakfast_id = _create("Pancakes", ["Breakfast"])
    _create("Boxing Day Stew", ["dinner"])

    for query in ("breakfast", "BREAKFAST", "BrEaKfAsT"):
        r = client.get("/recipes", params={"tag": query})
        assert r.status_code == 200
        assert [recipe["id"] for recipe in r.json()] == [breakfast_id]


def test_tag_filter_does_not_match_substrings():
    _create("Pancakes", ["breakfast"])

    for query in ("break", "breakfa", "breakfasts"):
        r = client.get("/recipes", params={"tag": query})
        assert r.status_code == 200
        assert r.json() == []


def test_tag_filter_preserves_id_ordering():
    first_id = _create("Pancakes", ["breakfast"])
    _create("Boxing Day Stew", ["dinner"])
    second_id = _create("Waffles", ["breakfast"])

    r = client.get("/recipes", params={"tag": "breakfast"})

    assert r.status_code == 200
    assert [recipe["id"] for recipe in r.json()] == [first_id, second_id]


def test_no_tag_returns_all_recipes():
    first_id = _create("Pancakes", ["breakfast"])
    second_id = _create("Boxing Day Stew", ["dinner"])

    r = client.get("/recipes")

    assert r.status_code == 200
    assert [recipe["id"] for recipe in r.json()] == [first_id, second_id]


def test_blank_tag_returns_400():
    for blank in ("", " ", "   ", "\t", "\n  "):
        r = client.get("/recipes", params={"tag": blank})
        assert r.status_code == 400, blank
        assert isinstance(r.json().get("detail"), str)
        assert r.json()["detail"]


def test_unknown_tag_returns_empty_list():
    _create("Pancakes", ["breakfast"])

    r = client.get("/recipes", params={"tag": "fish"})

    assert r.status_code == 200
    assert r.json() == []


def test_filtered_response_keeps_recipe_shape():
    _create("Pancakes", ["breakfast"], ingredients=["flour", "milk"])

    r = client.get("/recipes", params={"tag": "breakfast"})

    assert r.status_code == 200
    recipes = r.json()
    assert len(recipes) == 1
    assert set(recipes[0]) == {"id", "title", "ingredients", "tags"}
    assert recipes[0]["title"] == "Pancakes"
    assert recipes[0]["ingredients"] == ["flour", "milk"]
    assert recipes[0]["tags"] == ["breakfast"]
