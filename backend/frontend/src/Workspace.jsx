import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";

const fmt = (d) => (d ? new Date(d + "T00:00:00").toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" }) : "No date");
const today = () => new Date().toISOString().slice(0, 10);

const SUGGESTIONS = [
  "Add a task to submit the monthly report by Friday",
  "What's due this week?",
  "Mark the report done and add a task to start the next one",
  "Summarise my day",
];

function ToolChips({ calls }) {
  if (!calls?.length) return null;
  return (
    <div className="chips" aria-label="Tools the agent used">
      {calls.map((c, i) => (
        <code key={i} className={c.ok ? "chip" : "chip bad"} title={c.ok ? "Succeeded" : "Failed"}>
          {c.name}({Object.entries(c.arguments || {}).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(", ")})
        </code>
      ))}
    </div>
  );
}

export default function Workspace({ isAdmin }) {
  const [tasks, setTasks] = useState([]);
  const [loadErr, setLoadErr] = useState("");
  const [msgs, setMsgs] = useState([{ role: "assistant", content: isAdmin ? "Hi! Ask me to manage tasks, or assign one to a user by email." : "Hi! Tell me what to add, change or clear." }]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef(null);

  const refresh = useCallback(async () => {
    try { setTasks(await api("/tasks")); setLoadErr(""); } catch (e) { setLoadErr(e.message); }
  }, []);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, busy]);

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || busy) return;
    const history = msgs.filter((m) => !m.pending && !m.error).slice(1).map(({ role, content }) => ({ role, content }));
    setMsgs((m) => [...m, { role: "user", content: message }]);
    setInput(""); setBusy(true);
    try {
      const r = await api("/chat", { method: "POST", body: { message, history } });
      setMsgs((m) => [...m, { role: "assistant", content: r.reply, tool_calls: r.tool_calls, pending: r.pending_actions, error: r.error }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", content: e.message, error: true }]);
    }
    setBusy(false);
    refresh();
  }

  async function decide(msgIndex, action, verb) {
    try {
      const r = await api(`/chat/${verb}/${action.id}`, { method: "POST" });
      setMsgs((m) => m.map((x, i) => i !== msgIndex ? x : { ...x, pending: x.pending.filter((p) => p.id !== action.id), resolved: [...(x.resolved || []), r.message] }));
      refresh();
    } catch (e) {
      setMsgs((m) => m.map((x, i) => i !== msgIndex ? x : { ...x, pending: x.pending.filter((p) => p.id !== action.id), resolved: [...(x.resolved || []), e.message] }));
    }
  }

  async function toggle(t) {
    try { await api(`/tasks/${t.id}`, { method: "PATCH", body: { status: t.status === "done" ? "todo" : "done" } }); refresh(); } catch (e) { setLoadErr(e.message); }
  }

  const open = tasks.filter((t) => t.status !== "done");
  const done = tasks.filter((t) => t.status === "done");

  return (
    <div className="split">
      <section className="chat" aria-label="Chat with the agent">
        <div className="log" aria-live="polite">
          {msgs.map((m, i) => (
            <div key={i} className={`msg ${m.role}${m.error ? " err" : ""}`}>
              <p>{m.content}</p>
              <ToolChips calls={m.tool_calls} />
              {m.pending?.map((p) => (
                <div className="confirm" key={p.id}>
                  <p>{p.summary}</p>
                  <button className="danger" onClick={() => decide(i, p, "confirm")}>Delete</button>
                  <button className="ghost" onClick={() => decide(i, p, "cancel")}>Keep them</button>
                </div>
              ))}
              {m.resolved?.map((r, k) => <p key={k} className="resolved">{r}</p>)}
            </div>
          ))}
          {busy && <div className="msg assistant"><p className="muted">Working on it...</p></div>}
          <div ref={end} />
        </div>
        <div className="suggest">
          {SUGGESTIONS.map((s) => <button key={s} className="ghost small" onClick={() => send(s)} disabled={busy}>{s}</button>)}
        </div>
        <form className="composer" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="e.g. Add a task to call the vendor on Monday" maxLength={2000} aria-label="Message" />
          <button className="primary" disabled={busy || !input.trim()}>Send</button>
        </form>
      </section>

      <aside className="tasks" aria-label="Your tasks">
        <h2>Your tasks <span className="count">{open.length} open</span></h2>
        {loadErr && <p className="error">{loadErr}</p>}
        {!tasks.length && !loadErr && <p className="muted">Nothing here yet. Ask the agent to add your first task.</p>}
        <ul>
          {open.map((t) => (
            <li key={t.id} className={t.due_date && t.due_date < today() ? "overdue" : ""}>
              <input type="checkbox" checked={false} onChange={() => toggle(t)} aria-label={`Mark "${t.title}" done`} />
              <div><strong>{t.title}</strong><span className="meta">#{t.id} · {fmt(t.due_date)}{t.due_date && t.due_date < today() ? " (overdue)" : ""}</span></div>
              <span className={`prio ${t.priority}`}>{t.priority}</span>
            </li>
          ))}
        </ul>
        {done.length > 0 && <>
          <h3>Done</h3>
          <ul className="doneList">
            {done.map((t) => (
              <li key={t.id}>
                <input type="checkbox" checked onChange={() => toggle(t)} aria-label={`Mark "${t.title}" not done`} />
                <div><strong>{t.title}</strong><span className="meta">#{t.id}</span></div>
              </li>
            ))}
          </ul>
        </>}
      </aside>
    </div>
  );
}
