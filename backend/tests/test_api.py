"""Run: pytest -q   (uses a throwaway SQLite DB and a fake LLM, no network)"""
import json
import os
import types

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app import agent
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import User
from app.security import hash_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add(User(email="admin@t.dev", password_hash=hash_password("adminpass1"), role="admin"))
        db.commit()


def auth(email, pw="password123", signup=False):
    r = client.post("/auth/signup" if signup else "/auth/login", json={"email": email, "password": pw})
    assert r.status_code in (200, 201), r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def fake_llm(*scripted):
    """Each item is a list of (tool_name, args) calls, or a string for the final reply."""
    steps = iter(scripted)

    def create(**_):
        step = next(steps)
        if isinstance(step, str):
            msg = types.SimpleNamespace(content=step, tool_calls=None)
        else:
            calls = [types.SimpleNamespace(id=f"c{i}", function=types.SimpleNamespace(name=n, arguments=json.dumps(a)))
                     for i, (n, a) in enumerate(step)]
            msg = types.SimpleNamespace(content="", tool_calls=calls)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    return types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)))


def test_signup_is_always_user_role_and_ignores_role_field():
    r = client.post("/auth/signup", json={"email": "a@t.dev", "password": "password123", "role": "admin"})
    assert r.json()["role"] == "user"


def test_normal_user_gets_403_on_admin_api():
    h = auth("a@t.dev", signup=True)
    assert client.get("/admin/users", headers=h).status_code == 403
    assert client.get("/admin/tasks", headers=h).status_code == 403
    assert client.get("/admin/users").status_code == 401


def test_admin_can_list_users():
    h = auth("admin@t.dev", "adminpass1")
    assert client.get("/admin/users", headers=h).status_code == 200


def test_multi_step_agent_and_isolation(monkeypatch):
    h = auth("a@t.dev", signup=True)
    monkeypatch.setattr(agent, "get_client", lambda: fake_llm(
        [("add_task", {"title": "Report", "due_date": "2026-11-20", "user_id": 999})],
        [("add_task", {"title": "Start next report"}), ("list_tasks", {})],
        "Added both."))
    r = client.post("/chat", json={"message": "add two"}, headers=h).json()
    assert [c["name"] for c in r["tool_calls"]] == ["add_task", "add_task", "list_tasks"]
    assert len(client.get("/tasks", headers=h).json()) == 2
    # another user sees nothing and cannot update/delete a's task
    h2 = auth("b@t.dev", signup=True)
    assert client.get("/tasks", headers=h2).json() == []
    monkeypatch.setattr(agent, "get_client", lambda: fake_llm([("update_task", {"task_id": 1, "status": "done"})], "ok"))
    r = client.post("/chat", json={"message": "x"}, headers=h2).json()
    assert r["tool_calls"][0]["ok"] is False
    assert client.patch("/tasks/1", json={"status": "done"}, headers=h2).status_code == 404


def test_delete_requires_confirmation(monkeypatch):
    h = auth("a@t.dev", signup=True)
    monkeypatch.setattr(agent, "get_client", lambda: fake_llm([("add_task", {"title": "T"})], "ok"))
    client.post("/chat", json={"message": "add"}, headers=h)
    monkeypatch.setattr(agent, "get_client", lambda: fake_llm([("delete_tasks", {"task_ids": [1]})], "Please confirm."))
    r = client.post("/chat", json={"message": "delete all"}, headers=h).json()
    assert len(r["pending_actions"]) == 1
    assert len(client.get("/tasks", headers=h).json()) == 1  # still there
    pid = r["pending_actions"][0]["id"]
    h2 = auth("b@t.dev", signup=True)
    assert client.post(f"/chat/confirm/{pid}", headers=h2).status_code == 404  # not yours
    assert client.post(f"/chat/confirm/{pid}", headers=h).status_code == 200
    assert client.get("/tasks", headers=h).json() == []


def test_assign_task_admin_only(monkeypatch):
    auth("a@t.dev", signup=True)
    ha = auth("admin@t.dev", "adminpass1")
    monkeypatch.setattr(agent, "get_client", lambda: fake_llm([("assign_task", {"user_email": "a@t.dev", "title": "Do X"})], "Assigned."))
    assert client.post("/chat", json={"message": "assign"}, headers=ha).json()["tool_calls"][0]["ok"] is True
    hu = auth("a@t.dev")
    assert len(client.get("/tasks", headers=hu).json()) == 1
    monkeypatch.setattr(agent, "get_client", lambda: fake_llm([("assign_task", {"user_email": "a@t.dev", "title": "Hack"})], "no"))
    assert client.post("/chat", json={"message": "assign"}, headers=hu).json()["tool_calls"][0]["ok"] is False


def test_llm_failure_gives_friendly_message(monkeypatch):
    h = auth("a@t.dev", signup=True)

    def boom():
        c = fake_llm()
        c.chat.completions.create = lambda **_: (_ for _ in ()).throw(TimeoutError())
        return c

    monkeypatch.setattr(agent, "get_client", boom)
    r = client.post("/chat", json={"message": "hi"}, headers=h)
    assert r.status_code == 200 and r.json()["error"] is True
