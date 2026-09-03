import { useState } from "react";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth";

const QUICK = [
  { label: "Jane Doe (patient)", email: "jane.doe@example.com" },
  { label: "Dr. Mwangi (clinician)", email: "dr.mwangi@example.com" },
  { label: "Aisha (pharmacist)", email: "pharm@example.com" },
  { label: "Admin", email: "admin@example.com" },
];

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("jane.doe@example.com");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? "Invalid credentials." : "Login failed.");
    }
  };

  const seed = async () => {
    setSeeding(true);
    setError(null);
    try {
      await api.post("/demo/seed");
      setError("Demo data seeded. Password for all demo users is demo1234.");
    } catch {
      setError("Seed failed — is the backend running?");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="login-wrap">
      <div className="card login-card">
        <div className="brand" style={{ fontSize: 26 }}>
          M<span>H</span>S
        </div>
        <p className="sub">Mwafrika Health Services — investor demo</p>
        <form onSubmit={submit}>
          <label>Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          <button style={{ marginTop: 14, width: "100%" }}>Sign in</button>
        </form>

        <div className="quick-users" style={{ marginTop: 14 }}>
          <div className="muted" style={{ fontSize: 12 }}>
            Quick sign-in
          </div>
          {QUICK.map((q) => (
            <button
              key={q.email}
              className="secondary"
              onClick={() => {
                setEmail(q.email);
                setPassword("demo1234");
              }}
            >
              {q.label}
            </button>
          ))}
        </div>

        <button className="secondary" style={{ marginTop: 14, width: "100%" }} onClick={seed} disabled={seeding}>
          {seeding ? "Seeding…" : "Seed demo data"}
        </button>

        {error && (
          <div className="alert warn" style={{ marginTop: 12 }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
