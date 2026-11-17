import { useState } from "react";
import { api } from "./api.js";

export default function Login({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      onAuth(await api(`/auth/${mode}`, { method: "POST", body: { email, password } }));
    } catch (err) { setError(err.message); }
    setBusy(false);
  }

  return (
    <main className="login">
      <section className="login-card">
        <div className="brand big"><span className="mark" aria-hidden="true" />TaskPilot</div>
        <h1>Run your to-do list by talking to it.</h1>
        <p className="muted">Say what you need done. The agent adds, updates and clears tasks, and shows every step it took.</p>
        <form onSubmit={submit}>
          <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" /></label>
          <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
          {error && <p className="error" role="alert">{error}</p>}
          <button className="primary" disabled={busy}>{busy ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}</button>
        </form>
        <button className="link" onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }}>
          {mode === "login" ? "New here? Create an account" : "Have an account? Log in"}
        </button>
        <p className="tiny muted">The server runs on free hosting and may take about a minute to wake on your first request.</p>
      </section>
    </main>
  );
}
