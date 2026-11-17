"""Task tools the agent can call.

SAFETY MODEL: the LLM never supplies a user id. Every tool receives the authenticated
`user` from the backend and filters by it, so the model cannot touch another user's tasks
no matter what it is told. Admin-only tools re-check the role here as well.
"""
import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import PendingAction, Task, User

PRIORITIES = ("low", "medium", "high")

# --- JSON schemas shown to the LLM (note: no user_id anywhere) -----------------------
_DUE = {"type": "string", "description": "Due date as YYYY-MM-DD (resolve words like 'Friday' yourself)."}
_PRIO = {"type": "string", "enum": list(PRIORITIES)}

TOOL_SCHEMAS = {
    "add_task": {
        "description": "Create a new task for the current user.",
        "parameters": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "due_date": _DUE, "priority": _PRIO},
            "required": ["title"],
        },
    },
    "list_tasks": {
        "description": "List the current user's tasks. Always call this before updating or deleting if you do not know the task id.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["todo", "done", "all"]},
                "due_from": {**_DUE, "description": "Only tasks due on/after this date (YYYY-MM-DD)."},
                "due_to": {**_DUE, "description": "Only tasks due on/before this date (YYYY-MM-DD)."},
            },
        },
    },
    "update_task": {
        "description": "Update a task by id: change title, due date, priority, or mark it done/todo.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "title": {"type": "string"},
                "due_date": _DUE,
                "priority": _PRIO,
                "status": {"type": "string", "enum": ["todo", "done"]},
            },
            "required": ["task_id"],
        },
    },
    "delete_tasks": {
        "description": "Delete one or more tasks by id. The user must confirm before anything is deleted.",
        "parameters": {
            "type": "object",
            "properties": {"task_ids": {"type": "array", "items": {"type": "integer"}}},
            "required": ["task_ids"],
        },
    },
    "assign_task": {
        "description": "ADMIN ONLY. Create a task for another user, identified by their email.",
        "parameters": {
            "type": "object",
            "properties": {"user_email": {"type": "string"}, "title": {"type": "string"}, "due_date": _DUE, "priority": _PRIO},
            "required": ["user_email", "title"],
        },
    },
}
ADMIN_ONLY = {"assign_task"}
NEEDS_CONFIRMATION = {"delete_tasks"}


def schemas_for(user: User) -> list[dict]:
    return [
        {"type": "function", "function": {"name": n, **s}}
        for n, s in TOOL_SCHEMAS.items()
        if n not in ADMIN_ONLY or user.role == "admin"
    ]


def _parse_date(value) -> date | None:
    if value in (None, "", "null"):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD.")


def _prio(value) -> str:
    return value if value in PRIORITIES else "medium"


def _row(t: Task) -> dict:
    return {"id": t.id, "title": t.title, "due_date": t.due_date.isoformat() if t.due_date else None,
            "status": t.status, "priority": t.priority}


def _own_task(db: Session, user: User, task_id) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))


# --- Tool implementations -------------------------------------------------------------
def add_task(db: Session, user: User, title: str, due_date=None, priority=None) -> dict:
    title = (title or "").strip()
    if not title:
        raise ValueError("Task title is empty.")
    task = Task(user_id=user.id, title=title[:300], due_date=_parse_date(due_date), priority=_prio(priority))
    db.add(task)
    db.commit()
    return {"created": _row(task)}


def list_tasks(db: Session, user: User, status="all", due_from=None, due_to=None) -> dict:
    q = select(Task).where(Task.user_id == user.id)
    if status in ("todo", "done"):
        q = q.where(Task.status == status)
    if (d := _parse_date(due_from)):
        q = q.where(Task.due_date >= d)
    if (d := _parse_date(due_to)):
        q = q.where(Task.due_date <= d)
    tasks = db.scalars(q.order_by(Task.due_date.is_(None), Task.due_date, Task.id)).all()
    return {"count": len(tasks), "tasks": [_row(t) for t in tasks]}


def update_task(db: Session, user: User, task_id: int, title=None, due_date=None, priority=None, status=None) -> dict:
    task = _own_task(db, user, task_id)
    if task is None:
        raise ValueError(f"No task with id {task_id} found for this user.")
    if title:
        task.title = title.strip()[:300]
    if due_date is not None:
        task.due_date = _parse_date(due_date)
    if priority in PRIORITIES:
        task.priority = priority
    if status in ("todo", "done"):
        task.status = status
    db.commit()
    return {"updated": _row(task)}


def delete_tasks(db: Session, user: User, task_ids: list[int]) -> dict:
    deleted = []
    for tid in task_ids:
        task = _own_task(db, user, tid)
        if task:
            deleted.append(_row(task))
            db.delete(task)
    db.commit()
    return {"deleted": deleted, "count": len(deleted)}


def assign_task(db: Session, user: User, user_email: str, title: str, due_date=None, priority=None) -> dict:
    if user.role != "admin":  # defence in depth: tool is also hidden from non-admins
        raise PermissionError("Only admins can assign tasks to other users.")
    target = db.scalar(select(User).where(User.email == (user_email or "").strip().lower()))
    if target is None:
        raise ValueError(f"No user with email {user_email}.")
    task = Task(user_id=target.id, title=title.strip()[:300], due_date=_parse_date(due_date),
                priority=_prio(priority), assigned_by=user.id)
    db.add(task)
    db.commit()
    return {"assigned_to": target.email, "task": _row(task)}


IMPLEMENTATIONS = {f.__name__: f for f in (add_task, list_tasks, update_task, delete_tasks, assign_task)}


def execute_tool(db: Session, user: User, name: str, args: dict) -> dict:
    """Run a tool for `user`. Destructive tools are parked as a PendingAction instead."""
    if name not in IMPLEMENTATIONS or (name in ADMIN_ONLY and user.role != "admin"):
        raise ValueError(f"Unknown or forbidden tool: {name}")
    if name in NEEDS_CONFIRMATION:
        ids = [int(i) for i in args.get("task_ids", [])]
        owned = [_row(t) for t in (_own_task(db, user, i) for i in ids) if t]
        if not owned:
            raise ValueError("None of those task ids belong to this user.")
        titles = ", ".join(f"#{t['id']} {t['title']}" for t in owned)
        action = PendingAction(user_id=user.id, tool_name=name,
                               arguments=json.dumps({"task_ids": [t["id"] for t in owned]}),
                               summary=f"Delete {len(owned)} task(s): {titles}")
        db.add(action)
        db.commit()
        return {"status": "awaiting_user_confirmation", "pending_action_id": action.id,
                "note": "Nothing has been deleted yet. Tell the user to confirm or cancel."}
    return IMPLEMENTATIONS[name](db, user, **args)
