from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")  # "user" | "admin"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    tasks: Mapped[list["Task"]] = relationship(back_populates="owner", foreign_keys="Task.user_id")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="todo")  # "todo" | "done"
    priority: Mapped[str] = mapped_column(String(10), default="medium")  # low | medium | high
    assigned_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    owner: Mapped[User] = relationship(back_populates="tasks", foreign_keys=[user_id])


class PendingAction(Base):
    """A destructive action proposed by the agent, waiting for the user to confirm."""

    __tablename__ = "pending_actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(50))
    arguments: Mapped[str] = mapped_column(Text)  # JSON
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), default="pending")  # pending|confirmed|cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
