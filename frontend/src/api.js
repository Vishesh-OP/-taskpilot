const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export function getSession() {
  try { return JSON.parse(localStorage.getItem("tp_session")); } catch { return null; }
}
export function saveSession(s) {
  s ? localStorage.setItem("tp_session", JSON.stringify(s)) : localStorage.removeItem("tp_session");
}

export async function api(path, { method = "GET", body } = {}) {
  const session = getSession();
  let res;
  try {
    res = await fetch(BASE + path, {
      method,
      headers: { "Content-Type": "application/json", ...(session ? { Authorization: `Bearer ${session.access_token}` } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Can't reach the server. It may be waking up (free hosting) - wait a minute and try again.");
  }
  if (res.status === 401 && session && !path.startsWith("/auth")) {
    saveSession(null);
    window.location.reload();
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail) ? "Please check the email and password (min 8 characters)." : data.detail;
    throw new Error(detail || "Something went wrong.");
  }
  return data;
}
