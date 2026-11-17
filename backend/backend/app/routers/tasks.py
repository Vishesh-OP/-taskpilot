from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task, User
from ..schemas import TaskOut, TaskPatch
from ..security import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def my_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Task).where(Task.user_id == user.id).order_by(Task.status.desc(), Task.due_date.is_(None), Task.due_date, Task.id)
    return db.scalars(q).all()


@router.patch("/{task_id}", response_model=TaskOut)
def set_status(task_id: int, body: TaskPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if task is None:
        raise HTTPException(404, "Task not found.")
    task.status = body.status
    db.commit()
    return task
