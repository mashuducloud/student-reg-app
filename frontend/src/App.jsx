// src/App.jsx
import React, { useState } from "react";
import LoginForm from "./components/LoginForm.jsx";
import RegistrationForm from "./components/RegistrationForm.jsx";
import LearnersPage from "./components/LearnersPage.jsx";
import ProgrammesPage from "./components/ProgrammesPage.jsx";
import EnrolmentsPage from "./components/EnrolmentsPage.jsx";
import WorkplacePlacementsPage from "./components/WorkplacePlacementsPage.jsx";
import AttendancePage from "./components/AttendancePage.jsx";
import StipendsPage from "./components/StipendsPage.jsx";
import DocumentsPage from "./components/DocumentsPage.jsx";
import AssessmentsPage from "./components/AssessmentsPage.jsx";


// 🔑 Map Entra app roles → simple appRole used by the UI
function deriveAppRole(roles) {
  if (!roles || roles.length === 0) {
    return "learner"; // safe default
  }

  const normalized = roles.map((r) => String(r).toLowerCase());

  // Your ID token currently has: ["admin"] for the admin user
  if (normalized.includes("admin")) {
    return "admin";
  }

  // If you later use "learner" as a role value
  if (normalized.includes("learner")) {
    return "learner";
  }

  // Fallback – safer to default to learner than accidentally give admin
  return "learner";
}

// 📋 Menu entries per high-level role
const MENU_CONFIG = {
  admin: [
    { id: "overview", label: "Dashboard", section: "Main" },
    { id: "learners", label: "Manage Learners", section: "Learners" },
    { id: "register-learner", label: "Register Learner", section: "Learners" },
    { id: "programmes", label: "Programmes", section: "Programmes" },
    { id: "enrolments", label: "Enrolments", section: "Programmes" },
    { id: "workplace", label: "Workplace placements", section: "Workplace" },
    { id: "assessments", label: "Assessments & moderations", section: "Quality" },
    { id: "reports", label: "Reports & LMIS exports", section: "Reporting" },
  ],
  learner: [
    { id: "overview", label: "My dashboard", section: "Main" },
    { id: "my-profile", label: "My profile", section: "Learner" },
    { id: "my-enrolments", label: "My enrolments", section: "Learner" },
    { id: "my-attendance", label: "My attendance", section: "Learner" },
    { id: "my-stipends", label: "My stipends", section: "Learner" },
    { id: "my-documents", label: "My documents (PoE)", section: "Learner" },
  ],
};

function Dashboard({ session, onLogout }) {
  const appRole = session.appRole || "learner";
  const account = session.account;
  const menuItems = MENU_CONFIG[appRole];
  const [activePage, setActivePage] = useState("overview");

  // Build sidebar sections in order
  const sections = [];
  for (const item of menuItems) {
    if (!sections.includes(item.section)) {
      sections.push(item.section);
    }
  }

  const displayName =
    (account && (account.name || account.username || account.localAccountId)) ||
    "User";

  return (
    <div className="app-shell">
      {/* Top bar */}
      <header className="topbar">
        <div className="topbar-left">
          <div className="brand">
            <span className="brand-logo">MICT</span>
            <span className="brand-text">Learner Management</span>
          </div>
        </div>
        <div className="topbar-right">
          <span className="topbar-user">
            {displayName} · {appRole === "admin" ? "Provider / Admin" : "Learner"}
          </span>
          <button className="btn-link" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      {/* Body: sidebar + main content */}
      <div className="shell-body">
        {/* Sidebar */}
        <nav className="sidebar">
          {sections.map((section) => (
            <div key={section}>
              <div className="sidebar-section-label">{section}</div>
              {menuItems
                .filter((m) => m.section === section)
                .map((item) => (
                  <button
                    key={item.id}
                    className={
                      activePage === item.id
                        ? "sidebar-item sidebar-item-active"
                        : "sidebar-item"
                    }
                    onClick={() => setActivePage(item.id)}
                  >
                    {item.label}
                  </button>
                ))}
            </div>
          ))}
        </nav>

        {/* Main content */}
        <main className="shell-content">
          {/* === LANDING DASHBOARD === */}
          {activePage === "overview" && appRole === "admin" && (
            <section>
              <h1 className="page-title">Provider dashboard</h1>
              <p className="page-subtitle">
                Overview of learners, programmes and compliance for your organisation.
              </p>

              <div className="dashboard-grid">
                <div className="dashboard-card">
                  <div className="dashboard-card-label">Active learners</div>
                  <div className="dashboard-card-value">128</div>
                  <div className="dashboard-card-foot">
                    Demo data – connect to API later.
                  </div>
                </div>
                <div className="dashboard-card">
                  <div className="dashboard-card-label">Programmes running</div>
                  <div className="dashboard-card-value">9</div>
                  <div className="dashboard-card-foot">
                    Learnerships &amp; skills programmes.
                  </div>
                </div>
                <div className="dashboard-card">
                  <div className="dashboard-card-label">Completion rate</div>
                  <div className="dashboard-card-value">84%</div>
                  <div className="dashboard-card-foot">
                    Current intakes – demo.
                  </div>
                </div>
              </div>

              <div className="dashboard-panel">
                <h2 className="panel-title">Quick actions</h2>
                <ul className="quick-actions">
                  <li>✓ Approve new learner applications</li>
                  <li>✓ Capture attendance for today&apos;s sessions</li>
                  <li>✓ Export latest MICT LMIS datasets</li>
                </ul>
              </div>
            </section>
          )}

          {activePage === "overview" && appRole === "learner" && (
            <section>
              <h1 className="page-title">My learner dashboard</h1>
              <p className="page-subtitle">
                View your enrolments, attendance, assessments and stipend history.
              </p>

              <div className="dashboard-grid">
                <div className="dashboard-card">
                  <div className="dashboard-card-label">Current programme</div>
                  <div className="dashboard-card-value">Systems Development</div>
                  <div className="dashboard-card-foot">
                    Demo value – wire to API later.
                  </div>
                </div>
                <div className="dashboard-card">
                  <div className="dashboard-card-label">Attendance</div>
                  <div className="dashboard-card-value">92%</div>
                  <div className="dashboard-card-foot">
                    Last 30 days – demo data.
                  </div>
                </div>
                <div className="dashboard-card">
                  <div className="dashboard-card-label">Latest stipend status</div>
                  <div className="dashboard-card-value">Approved</div>
                  <div className="dashboard-card-foot">
                    Last month – demo.
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* === ADMIN: Register learner === */}
          {activePage === "register-learner" && appRole === "admin" && (
            <section>
              <h1 className="page-title">Register a learner</h1>
              <p className="page-subtitle">
                Capture a learner for a MICT SETA–aligned programme.
              </p>

              <div className="card card-inner">
                <RegistrationForm onLogout={onLogout} />
              </div>
            </section>
          )}

          {/* ADMIN pages */}
          {activePage === "learners" && appRole === "admin" && <LearnersPage />}

          {activePage === "programmes" && appRole === "admin" && (
            <ProgrammesPage />
          )}

          {activePage === "enrolments" && appRole === "admin" && (
            <EnrolmentsPage />
          )}

          {activePage === "workplace" && appRole === "admin" && (
            <WorkplacePlacementsPage />
          )}

          {activePage === "assessments" && appRole === "admin" && (
            <AssessmentsPage />
          )}

          {activePage === "reports" && appRole === "admin" && (
            <section>
              <h1 className="page-title">Reports &amp; LMIS exports</h1>
              <p className="page-subtitle">
                Generate MICT LMIS-aligned CSV/Excel exports.
              </p>
            </section>
          )}

          {/* LEARNER pages */}
          {activePage === "my-profile" && appRole === "learner" && (
            <section>
              <h1 className="page-title">My profile</h1>
              <p className="page-subtitle">
                View and update your personal information and documents.
              </p>
            </section>
          )}

          {activePage === "my-enrolments" && appRole === "learner" && (
            <section>
              <h1 className="page-title">My enrolments</h1>
              <p className="page-subtitle">
                See which programmes you&apos;re enrolled in and statuses.
              </p>
            </section>
          )}

          {activePage === "my-attendance" && appRole === "learner" && (
            <AttendancePage />
          )}

          {activePage === "my-stipends" && appRole === "learner" && (
            <StipendsPage />
          )}

          {activePage === "my-documents" && appRole === "learner" && (
            <DocumentsPage />
          )}
        </main>
      </div>
    </div>
  );
}

function App() {
  const [session, setSession] = useState(null);
  const isLoggedIn = !!session;

  const handleLogin = ({ account, roles }) => {
    const appRole = deriveAppRole(roles);
    setSession({ account, roles, appRole });
  };

  const handleLogout = () => {
    setSession(null);
  };

  // 🔐 BEFORE LOGIN: centered auth card
  if (!isLoggedIn) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <LoginForm onLogin={handleLogin} />
        </div>
      </div>
    );
  }

  // 📊 AFTER LOGIN: full app shell, no outer frame
  return <Dashboard session={session} onLogout={handleLogout} />;
}

export default App;
