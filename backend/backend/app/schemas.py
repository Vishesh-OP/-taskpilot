from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    due_date: date | None
    status: str
    priority: str


class AdminTaskOut(TaskOut):
    owner_email: str


class AdminUserOut(BaseModel):
    id: int
    email: str
    role: str
    task_count: int


class TaskPatch(BaseModel):
    status: str = Field(pattern="^(todo|done)$")


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=4000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
