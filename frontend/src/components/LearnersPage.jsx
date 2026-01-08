// src/components/LearnersPage.jsx
import React, { useEffect, useState } from "react";
import { getTokenForApi } from "../authClient";

function LearnersPage() {
  const [learners, setLearners] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  // Form / edit state (mirrors ProgrammesPage)
  const [editingLearnerId, setEditingLearnerId] = useState(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  // Delete state
  const [deleteError, setDeleteError] = useState("");

  const isEditing = editingLearnerId !== null;

  const apiBase =
    window.location.hostname === "localhost"
      ? "http://localhost:5000"
      : "http://student-app:5000";

  // Fetch learners on mount
  useEffect(() => {
    const fetchLearners = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const token = await getTokenForApi();
        const url = `${apiBase}/students`;

        const resp = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.error || `Failed: ${resp.status}`);
        }

        const data = await resp.json();
        setLearners(data || []);
        setFiltered(data || []);
      } catch (err) {
        console.error("Failed to load learners", err);
        setLoadError(err.message || "Failed to load learners");
      } finally {
        setLoading(false);
      }
    };

    fetchLearners();
  }, [apiBase]);

  // Client-side search (same pattern as ProgrammesPage)
  useEffect(() => {
    const term = search.toLowerCase().trim();
    if (!term) {
      setFiltered(learners);
      return;
    }

    setFiltered(
      learners.filter((l) => {
        const fn = (l.first_name || "").toLowerCase();
        const ln = (l.last_name || "").toLowerCase();
        const em = (l.email || "").toLowerCase();
        const combined = `${fn} ${ln} ${em}`;
        return (
          fn.includes(term) ||
          ln.includes(term) ||
          em.includes(term) ||
          combined.includes(term)
        );
      })
    );
  }, [search, learners]);

  // Helpers
  const resetForm = () => {
    setFirstName("");
    setLastName("");
    setEmail("");
  };

  const cancelEdit = () => {
    setEditingLearnerId(null);
    resetForm();
    setSaveError("");
    setSaveMessage("");
  };

  // When a row is clicked, populate the form and enter edit mode
  const handleRowClick = (learner) => {
    setEditingLearnerId(learner.id || null);
    setFirstName(learner.first_name || "");
    setLastName(learner.last_name || "");
    setEmail(learner.email || "");
    setSaveError("");
    setSaveMessage("");
  };

  // Create / update submit handler (shared form)
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaveError("");
    setSaveMessage("");
    setDeleteError("");
    setSaving(true);

    try {
      const token = await getTokenForApi();
      const url = isEditing
        ? `${apiBase}/students/${editingLearnerId}`
        : `${apiBase}/students`;

      const resp = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email,
        }),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      const returnedLearner = data.student;

      if (isEditing) {
        const updated = returnedLearner || {
          id: editingLearnerId,
          first_name: firstName,
          last_name: lastName,
          email,
        };

        setLearners((prev) =>
          prev.map((l) => (l.id === updated.id ? updated : l))
        );

        // After successful save, clear inputs and deselect the row
        cancelEdit();

        setSaveMessage("Learner updated successfully.");
      } else {
        const newLearner = returnedLearner || {
          id: data.id,
          first_name: firstName,
          last_name: lastName,
          email,
        };

        setLearners((prev) => [...prev, newLearner]);
        resetForm();
        setSaveMessage("Learner created successfully.");
      }

      // Auto-hide toast
      setTimeout(() => {
        setSaveMessage("");
      }, 3000);
    } catch (err) {
      console.error("Failed to save learner", err);
      setSaveError(err.message || "Failed to save learner.");
    } finally {
      setSaving(false);
    }
  };

  // Delete handler
  const handleDelete = async (learner) => {
    setDeleteError("");

    const confirmDelete = window.confirm(
      `Delete learner "${learner.first_name} ${learner.last_name}"?`
    );
    if (!confirmDelete) return;

    try {
      const token = await getTokenForApi();
      const url = `${apiBase}/students/${learner.id}`;

      const resp = await fetch(url, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      setLearners((prev) => prev.filter((l) => l.id !== learner.id));

      // If we were editing this learner, exit edit mode & clear form
      if (editingLearnerId === learner.id) {
        cancelEdit();
      }
    } catch (err) {
      console.error("Failed to delete learner", err);
      setDeleteError(err.message || "Failed to delete learner.");
    }
  };

  return (
    <section>
      {/* Header + search: same structure/classes as ProgrammesPage */}
      <div className="learners-header">
        <div>
          <h1 className="page-title">Learners</h1>
          <p className="page-subtitle">
            Maintain registered learners for all programmes.
          </p>
        </div>

        <div className="learners-search">
          <label htmlFor="learner-search">Search</label>
          <input
            id="learner-search"
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Create / Edit card (shared form) – same visual pattern as ProgrammesPage */}
      <div className="learners-edit-card">
        <div className="learners-edit-header">
          <div>
            <h2 className="panel-title">
              {isEditing
                ? `Update learner #${editingLearnerId}`
                : "Create new learner"}
            </h2>
            <span className="badge">
              {isEditing ? "Edit mode" : "Create mode"}
            </span>
          </div>

          {isEditing && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={cancelEdit}
            >
              Cancel
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-field">
              <label htmlFor="learner_first_name">First name</label>
              <input
                id="learner_first_name"
                type="text"
                value={firstName}
                onChange={(e) => {
                  setFirstName(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              />
            </div>
            <div className="form-field">
              <label htmlFor="learner_last_name">Last name</label>
              <input
                id="learner_last_name"
                type="text"
                value={lastName}
                onChange={(e) => {
                  setLastName(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="learner_email">Email</label>
              <input
                id="learner_email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              />
            </div>
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={saving}
            >
              {saving
                ? isEditing
                  ? "Saving..."
                  : "Saving..."
                : isEditing
                ? "Save changes"
                : "Save learner"}
            </button>
          </div>
        </form>

        {saveError && <div className="message message-error">{saveError}</div>}
      </div>

      {loading && <p>Loading…</p>}

      {loadError && !loading && (
        <div className="message message-error">
          Error loading learners: {loadError}
        </div>
      )}

      {deleteError && (
        <div className="message message-error">
          Error deleting learner: {deleteError}
        </div>
      )}

      {!loading && !loadError && filtered.length === 0 && (
        <p>No learners found.</p>
      )}

      {!loading && !loadError && filtered.length > 0 && (
        <div className="table-wrapper">
          <table className="table learners-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>First name</th>
                <th>Last name</th>
                <th>Email</th>
                <th style={{ width: "1%", whiteSpace: "nowrap" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((l) => (
                <tr
                  key={l.id}
                  onClick={() => handleRowClick(l)}
                  className={
                    editingLearnerId === l.id
                      ? "table-row-editing"
                      : undefined
                  }
                  style={{ cursor: "pointer" }}
                >
                  <td>{l.id}</td>
                  <td>{l.first_name}</td>
                  <td>{l.last_name}</td>
                  <td>{l.email}</td>
                  <td>
                    <div className="table-actions">
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRowClick(l);
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(l);
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Save confirmation toast – same as ProgrammesPage */}
      {saveMessage && <div className="toast toast-success">{saveMessage}</div>}
    </section>
  );
}

export default LearnersPage;
