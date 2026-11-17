"""Create the demo admin + demo user (idempotent). Run: python -m scripts.seed"""
import os
from datetime import date, timedelta

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Task, User
from app.security import hash_password


def upsert(db, email, password, role):
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(password), role=role)
        db.add(user)
        db.commit()
    else:  # re-running the seed also resets password/role
        user.password_hash, user.role = hash_password(password), role
        db.commit()
    return user


def main():
    Base.metadata.create_all(engine)
    admin_pw, demo_pw = os.environ.get("ADMIN_PASSWORD"), os.environ.get("DEMO_PASSWORD")
    if not admin_pw or not demo_pw:
        raise SystemExit("Set ADMIN_PASSWORD and DEMO_PASSWORD in the environment first.")
    with SessionLocal() as db:
        upsert(db, os.environ.get("ADMIN_EMAIL", "admin@taskpilot.dev"), admin_pw, "admin")
        demo = upsert(db, os.environ.get("DEMO_EMAIL", "user@taskpilot.dev"), demo_pw, "user")
        if not db.scalar(select(Task).where(Task.user_id == demo.id)):
            today = date.today()
            db.add_all([
                Task(user_id=demo.id, title="Prepare monthly report", due_date=today + timedelta(days=2), priority="high"),
                Task(user_id=demo.id, title="Review team leave requests", due_date=today + timedelta(days=4)),
                Task(user_id=demo.id, title="Book travel for client visit", priority="low"),
                Task(user_id=demo.id, title="Send invoice to vendor", due_date=today - timedelta(days=1), status="done"),
            ])
            db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    main()
