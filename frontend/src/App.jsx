import { useState } from "react";
import { getSession, saveSession } from "./api.js";
import Login from "./Login.jsx";
import Workspace from "./Workspace.jsx";
import Admin from "./Admin.jsx";

export default function App() {
  const [session, setSession] = useState(getSession());
  const [page, setPage] = useState("workspace");

  const onAuth = (s) => { saveSession(s); setSession(s); setPage("workspace"); };
  const logout = () => { saveSession(null); setSession(null); };

  if (!session) return <Login onAuth={onAuth} />;
  const isAdmin = session.role === "admin";

  return (
    <div className="app">
      <header className="top">
        <div className="brand"><span className="mark" aria-hidden="true" />TaskPilot</div>
        <nav>
          <button className={page === "workspace" ? "tab on" : "tab"} onClick={() => setPage("workspace")}>Workspace</button>
          {isAdmin && <button className={page === "admin" ? "tab on" : "tab"} onClick={() => setPage("admin")}>All users and tasks</button>}
        </nav>
        <div className="who">
          <span>{session.email}</span>
          <span className={isAdmin ? "pill admin" : "pill"}>{session.role}</span>
          <button className="ghost" onClick={logout}>Log out</button>
        </div>
      </header>
      {page === "admin" && isAdmin ? <Admin /> : <Workspace isAdmin={isAdmin} />}
    </div>
  );
}
