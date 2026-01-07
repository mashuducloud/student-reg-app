// src/components/DocumentsPage.jsx
import React, { useEffect, useState } from "react";
import { getTokenForApi } from "../authClient";

function DocumentsPage() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    const fetchDocs = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const token = await getTokenForApi();
        const apiBase =
          window.location.hostname === "localhost"
            ? "http://localhost:5000"
            : "http://student-app:5000";

        const url = `${apiBase}/documents`; // TODO backend

        const resp = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.error || `Failed: ${resp.status}`);
        }

        const data = await resp.json();
        setDocs(data || []);
      } catch (err) {
        console.error("Failed to load documents", err);
        setLoadError(err.message || "Failed to load documents");
      } finally {
        setLoading(false);
      }
    };

    fetchDocs();
  }, []);

  return (
    <section>
      <h1 className="page-title">Documents</h1>
      <p className="page-subtitle">
        Uploaded documents / PoE per learner (read-only list for now).
      </p>

      {loading && <p>Loading…</p>}
      {loadError && !loading && (
        <div className="message message-error">
          Error loading documents: {loadError}
        </div>
      )}

      {!loading && !loadError && docs.length === 0 && (
        <p>No documents found.</p>
      )}

      {!loading && !loadError && docs.length > 0 && (
        <div className="table-wrapper">
          <table className="table learners-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Student ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Path</th>
                <th>Uploaded at</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td>{d.id}</td>
                  <td>{d.student_id}</td>
                  <td>{d.document_name}</td>
                  <td>{d.document_type}</td>
                  <td>{d.file_path}</td>
                  <td>{d.uploaded_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default DocumentsPage;
