import { useEffect, useState } from "react";
import { api } from "./api.js";

export default function Admin() {
  const [users, setUsers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api("/admin/users"), api("/admin/tasks")])
      .then(([u, t]) => { setUsers(u); setTasks(t); })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="admin">
      {error && <p className="error">{error}</p>}
      <section>
        <h2>Users <span className="count">{users.length}</span></h2>
        <table>
          <thead><tr><th>Email</th><th>Role</th><th>Tasks</th></tr></thead>
          <tbody>{users.map((u) => <tr key={u.id}><td>{u.email}</td><td>{u.role}</td><td>{u.task_count}</td></tr>)}</tbody>
        </table>
      </section>
      <section>
        <h2>All tasks <span className="count">{tasks.length}</span></h2>
        <div className="scroll">
          <table>
            <thead><tr><th>Owner</th><th>Task</th><th>Due</th><th>Priority</th><th>Status</th></tr></thead>
            <tbody>{tasks.map((t) => (
              <tr key={t.id}><td>{t.owner_email}</td><td>{t.title}</td><td>{t.due_date || "-"}</td><td>{t.priority}</td><td>{t.status}</td></tr>
            ))}</tbody>
          </table>
        </div>
        <p className="muted tiny">To give a user a task, tell the agent in the Workspace tab: "Assign 'Prepare Q4 deck' to user@taskpilot.dev by Friday".</p>
      </section>
    </div>
  );
}
