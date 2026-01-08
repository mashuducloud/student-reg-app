// src/components/AttendancePage.jsx
import React, { useEffect, useState } from "react";
import { getTokenForApi } from "../authClient";

function AttendancePage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    const fetchAttendance = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const token = await getTokenForApi();
        const apiBase =
          window.location.hostname === "localhost"
            ? "http://localhost:5000"
            : "http://student-app:5000";

        const url = `${apiBase}/attendance`; // TODO backend

        const resp = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.error || `Failed: ${resp.status}`);
        }

        const data = await resp.json();
        setRows(data || []);
      } catch (err) {
        console.error("Failed to load attendance", err);
        setLoadError(err.message || "Failed to load attendance");
      } finally {
        setLoading(false);
      }
    };

    fetchAttendance();
  }, []);

  return (
    <section>
      <h1 className="page-title">Attendance</h1>
      <p className="page-subtitle">
        Daily attendance records per learner.
      </p>

      {loading && <p>Loading…</p>}
      {loadError && !loading && (
        <div className="message message-error">
          Error loading attendance: {loadError}
        </div>
      )}

      {!loading && !loadError && rows.length === 0 && (
        <p>No attendance records found.</p>
      )}

      {!loading && !loadError && rows.length > 0 && (
        <div className="table-wrapper">
          <table className="table learners-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Student ID</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>{r.id}</td>
                  <td>{r.student_id}</td>
                  <td>{r.attendance_date}</td>
                  <td>{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default AttendancePage;
