"""Per-test database isolation.

``main.DB_PATH`` is read on every ``get_db()`` call, so pointing it at ``tmp_path`` gives
each test its own SQLite file. The starter's tests otherwise share one ``recipes.db``.
"""

import pytest

import main


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "recipes.db")
    main.init_db()
    yield
