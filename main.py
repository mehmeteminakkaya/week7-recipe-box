"""Recipe Box — starter app for Week 7.

A tiny FastAPI service for recipes and tags, with a static frontend. Use it as the
playground for concurrent multi-agent work and a generator-critic loop.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload
    # open http://localhost:8000/
Test:
    pytest
"""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE = Path(__file__).parent
DB_PATH = BASE / "recipes.db"

app = FastAPI(title="Recipe Box")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_db()) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS recipes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                ingredients TEXT NOT NULL,  -- JSON list of strings
                tags        TEXT NOT NULL   -- JSON list of strings
            )""")
        conn.commit()


init_db()


class RecipeIn(BaseModel):
    title: str
    ingredients: list[str] = []
    tags: list[str] = []


def _row_to_recipe(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "ingredients": json.loads(row["ingredients"]),
        "tags": json.loads(row["tags"]),
    }


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.post("/recipes")
def create_recipe(recipe: RecipeIn):
    with closing(get_db()) as conn:
        cur = conn.execute(
            "INSERT INTO recipes (title, ingredients, tags) VALUES (?, ?, ?)",
            (recipe.title, json.dumps(recipe.ingredients), json.dumps(recipe.tags)),
        )
        conn.commit()
        rid = cur.lastrowid
    return {"id": rid, **recipe.model_dump()}


@app.get("/recipes")
def list_recipes(tag: str | None = None):
    """List recipes ordered by id, optionally filtered by one exact tag.

    ``tag`` is matched case-insensitively and exactly (not as a substring); surrounding
    whitespace is ignored. Omitting it returns every recipe. A present but blank (or
    whitespace-only) value is a 400 instead of silently returning everything.
    """
    if tag is not None and not tag.strip():
        raise HTTPException(status_code=400, detail="tag must not be blank")
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT * FROM recipes ORDER BY id").fetchall()
    recipes = [_row_to_recipe(r) for r in rows]
    if tag is None:
        return recipes
    wanted = tag.strip().casefold()
    return [recipe for recipe in recipes if any(t.casefold() == wanted for t in recipe["tags"])]


@app.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    with closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="unknown recipe")
    return _row_to_recipe(row)


SQLITE_INT_MIN = -(2**63)
SQLITE_INT_MAX = 2**63 - 1


def _parse_recipe_ids(ids: str | None) -> list[int]:
    """Turn the comma-separated ``ids`` query value into a list of recipe ids."""
    if ids is None or not ids.replace(",", "").strip():
        raise HTTPException(
            status_code=400,
            detail="query parameter 'ids' must be a non-empty comma-separated list of recipe ids",
        )
    recipe_ids: list[int] = []
    for token in ids.split(","):
        token = token.strip()
        digits = token[1:] if token[:1] in {"+", "-"} else token
        if not digits.isascii() or not digits.isdecimal():
            raise HTTPException(
                status_code=400,
                detail=f"invalid recipe id: {token!r}",
            )
        recipe_ids.append(int(token))
    return recipe_ids


def _ingredients_by_id(recipe_ids: list[int]) -> dict[int, list[str]]:
    """Fetch ``{recipe id: ingredients}`` for ids that can be stored in SQLite."""
    queryable = [rid for rid in recipe_ids if SQLITE_INT_MIN <= rid <= SQLITE_INT_MAX]
    if not queryable:
        return {}
    placeholders = ", ".join("?" for _ in queryable)
    with closing(get_db()) as conn:
        rows = conn.execute(
            f"SELECT id, ingredients FROM recipes WHERE id IN ({placeholders})",
            queryable,
        ).fetchall()
    return {row["id"]: json.loads(row["ingredients"]) for row in rows}


@app.get("/shopping-list")
def shopping_list(ids: str | None = None):
    """Merge the ingredients of the requested recipes into a shopping list.

    ``ids`` is a comma-separated list of recipe ids (``?ids=1,2,3``). The response is
    ``{"items": [...]}`` with ingredients in first-seen order across the requested
    recipes, de-duplicated case-insensitively while keeping the first spelling.
    Missing or blank ``ids`` and non-integer tokens are 400; unknown ids are 404.
    """
    requested_ids = list(dict.fromkeys(_parse_recipe_ids(ids)))
    ingredients_by_id = _ingredients_by_id(requested_ids)
    unknown_ids = [rid for rid in requested_ids if rid not in ingredients_by_id]
    if unknown_ids:
        unknown = ", ".join(str(rid) for rid in unknown_ids)
        raise HTTPException(status_code=404, detail=f"unknown recipe ids: {unknown}")

    items: list[str] = []
    seen: set[str] = set()
    for rid in requested_ids:
        for ingredient in ingredients_by_id[rid]:
            key = ingredient.casefold()
            if key not in seen:
                seen.add(key)
                items.append(ingredient)
    return {"items": items}
