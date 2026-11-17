from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task, User
from ..schemas import AdminTaskOut, AdminUserOut
from ..security import require_admin

# Every route in this router requires an admin, enforced by the backend.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[AdminUserOut])
def all_users(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Task.user_id, func.count(Task.id)).group_by(Task.user_id)).all())
    return [AdminUserOut(id=u.id, email=u.email, role=u.role, task_count=counts.get(u.id, 0))
            for u in db.scalars(select(User).order_by(User.id))]


@router.get("/tasks", response_model=list[AdminTaskOut])
def all_tasks(db: Session = Depends(get_db)):
    rows = db.execute(select(Task, User.email).join(User, Task.user_id == User.id).order_by(Task.id.desc())).all()
    return [AdminTaskOut(**{c: getattr(t, c) for c in ("id", "title", "due_date", "status", "priority")}, owner_email=e)
            for t, e in rows]
