import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Login from "./pages/Login";
import PatientBooking from "./pages/PatientBooking";
import Visit from "./pages/Visit";
import ProviderConsole from "./pages/ProviderConsole";
import PharmacyBoard from "./pages/PharmacyBoard";
import MetricsDashboard from "./pages/MetricsDashboard";

function Shell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          M<span>H</span>S
        </div>
        <nav className="nav">
          <NavLink to="/book">Book &amp; Intake</NavLink>
          <NavLink to="/console">Provider Console</NavLink>
          <NavLink to="/pharmacy">Pharmacy Board</NavLink>
          <NavLink to="/metrics">Metrics</NavLink>
        </nav>
        <div className="spacer" />
        <div className="userbox">
          {user && (
            <>
              <div>
                {user.first_name} {user.last_name}
              </div>
              <div className="muted">{user.role}</div>
              <button className="secondary" style={{ marginTop: 8 }} onClick={logout}>
                Sign out
              </button>
            </>
          )}
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <div className="login-wrap">Loading…</div>;
  if (!user) return <Login />;

  return (
    <Shell>
      <Routes>
        <Route path="/book" element={<PatientBooking />} />
        <Route path="/visit/:appointmentId" element={<Visit />} />
        <Route path="/console" element={<ProviderConsole />} />
        <Route path="/pharmacy" element={<PharmacyBoard />} />
        <Route path="/metrics" element={<MetricsDashboard />} />
        <Route path="*" element={<Navigate to={landingFor(user.role)} replace />} />
      </Routes>
    </Shell>
  );
}

function landingFor(role: string) {
  if (role === "clinician" || role === "chw") return "/console";
  if (role === "pharmacist") return "/pharmacy";
  if (role === "admin") return "/metrics";
  return "/book";
}
