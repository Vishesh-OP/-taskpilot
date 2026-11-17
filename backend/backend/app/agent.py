"""The agent loop: LLM -> tool calls -> results -> LLM ... until it answers in plain text."""
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from .config import settings
from .models import User
from .tools import execute_tool, schemas_for

log = logging.getLogger("taskpilot.agent")

FRIENDLY_ERROR = "The AI assistant is busy or unavailable right now. Please try again in a moment."


def get_client():
    from groq import Groq

    return Groq(api_key=settings.groq_api_key, timeout=settings.llm_timeout_seconds, max_retries=1)


def system_prompt(user: User) -> str:
    now = datetime.now(ZoneInfo(settings.timezone))
    admin_line = (
        "The user is an ADMIN: you may also use assign_task to create tasks for other users by email.\n"
        if user.role == "admin" else ""
    )
    return (
        "You are TaskPilot, an assistant that manages the user's to-do list using tools.\n"
        f"Today is {now.strftime('%A, %Y-%m-%d')} ({settings.timezone}, current time {now.strftime('%H:%M')}). "
        "Convert relative dates ('tomorrow', 'by Friday', 'next Monday') to YYYY-MM-DD from today's date. "
        "'By Friday' on a weekday before Friday means this coming Friday; 'next Monday' means the Monday of next week.\n"
        f"{admin_line}"
        "Rules:\n"
        "- Always use tools to read or change tasks; never invent task data.\n"
        "- If you need a task id, call list_tasks first. If several tasks match, ask which one.\n"
        "- Handle multi-part requests by calling every needed tool.\n"
        "- Deleting requires user confirmation: call delete_tasks, then tell the user to press Confirm or Cancel. "
        "Never claim something is deleted until confirmed.\n"
        "- Keep replies short and say exactly what you did."
    )


def run_agent(db: Session, user: User, message: str, history: list[dict], client=None) -> dict:
    client = client or get_client()
    messages = [{"role": "system", "content": system_prompt(user)}, *history, {"role": "user", "content": message}]
    tools = schemas_for(user)
    trace, pending_ids = [], []

    for _ in range(settings.max_agent_steps):
        try:
            resp = client.chat.completions.create(
                model=settings.groq_model, messages=messages, tools=tools,
                tool_choice="auto", temperature=0.2, max_tokens=800,
            )
        except Exception:  # timeouts, rate limits, malformed tool calls, network errors
            log.exception("LLM call failed")
            return {"reply": FRIENDLY_ERROR, "tool_calls": trace, "pending_actions": pending_ids, "error": True}

        msg = resp.choices[0].message
        if not msg.tool_calls:
            return {"reply": (msg.content or "Done.").strip(), "tool_calls": trace,
                    "pending_actions": pending_ids, "error": False}

        messages.append({
            "role": "assistant", "content": msg.content or "",
            "tool_calls": [{"id": c.id, "type": "function",
                            "function": {"name": c.function.name, "arguments": c.function.arguments}}
                           for c in msg.tool_calls],
        })
        for call in msg.tool_calls:
            name, args = call.function.name, {}
            try:
                args = json.loads(call.function.arguments or "{}")
                args.pop("user_id", None)  # never let the model choose whose data to touch
                result = execute_tool(db, user, name, args)
                ok = True
            except Exception as exc:  # report tool errors back to the model so it can recover
                db.rollback()
                result, ok = {"error": str(exc)}, False
            if isinstance(result, dict) and result.get("pending_action_id"):
                pending_ids.append(result["pending_action_id"])
            trace.append({"name": name, "arguments": args, "ok": ok})
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, default=str)})

    return {"reply": "That request needed too many steps. Please try a simpler one.",
            "tool_calls": trace, "pending_actions": pending_ids, "error": False}
