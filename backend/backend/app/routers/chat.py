import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agent import run_agent
from ..database import get_db
from ..models import PendingAction, User
from ..schemas import ChatIn
from ..security import get_current_user
from ..tools import IMPLEMENTATIONS

router = APIRouter(prefix="/chat", tags=["chat"])


def _pending_payload(db: Session, ids: list[int]) -> list[dict]:
    rows = db.scalars(select(PendingAction).where(PendingAction.id.in_(ids))).all() if ids else []
    return [{"id": a.id, "summary": a.summary} for a in rows]


@router.post("")
def chat(body: ChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = [m.model_dump() for m in body.history[-10:]]
    result = run_agent(db, user, body.message, history)
    return {"reply": result["reply"], "tool_calls": result["tool_calls"],
            "pending_actions": _pending_payload(db, result["pending_actions"]), "error": result["error"]}


def _get_pending(db: Session, user: User, action_id: int) -> PendingAction:
    # Scoped to the logged-in user: you cannot confirm someone else's action.
    action = db.scalar(select(PendingAction).where(PendingAction.id == action_id, PendingAction.user_id == user.id))
    if action is None or action.status != "pending":
        raise HTTPException(404, "This action no longer exists or was already handled.")
    return action


@router.post("/confirm/{action_id}")
def confirm(action_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    action = _get_pending(db, user, action_id)
    result = IMPLEMENTATIONS[action.tool_name](db, user, **json.loads(action.arguments))
    action.status = "confirmed"
    db.commit()
    return {"message": f"Deleted {result['count']} task(s).", "result": result}


@router.post("/cancel/{action_id}")
def cancel(action_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    action = _get_pending(db, user, action_id)
    action.status = "cancelled"
    db.commit()
    return {"message": "Cancelled. Nothing was deleted."}
