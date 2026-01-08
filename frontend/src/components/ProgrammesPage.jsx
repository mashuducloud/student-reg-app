// src/components/ProgrammesPage.jsx
import React, { useEffect, useState } from "react";
import { getTokenForApi } from "../authClient";

function ProgrammesPage() {
  const [programmes, setProgrammes] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  // Form / edit state
  const [editingProgrammeId, setEditingProgrammeId] = useState(null);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [nqfLevel, setNqfLevel] = useState("");
  const [credits, setCredits] = useState("");
  const [description, setDescription] = useState("");

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  // Delete state
  const [deleteError, setDeleteError] = useState("");

  const isEditing = editingProgrammeId !== null;

  const apiBase =
    window.location.hostname === "localhost"
      ? "http://localhost:5000"
      : "http://student-app:5000";

  // Fetch programmes on mount
  useEffect(() => {
    const fetchProgrammes = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const token = await getTokenForApi();
        const url = `${apiBase}/programmes`;

        const resp = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.error || `Failed: ${resp.status}`);
        }

        const data = await resp.json();
        setProgrammes(data || []);
        setFiltered(data || []);
      } catch (err) {
        console.error("Failed to load programmes", err);
        setLoadError(err.message || "Failed to load programmes");
      } finally {
        setLoading(false);
      }
    };

    fetchProgrammes();
  }, [apiBase]);

  // Client-side search (like LearnersPage)
  useEffect(() => {
    const term = search.toLowerCase().trim();
    if (!term) {
      setFiltered(programmes);
      return;
    }

    setFiltered(
      programmes.filter((p) => {
        const name = (p.programme_name || "").toLowerCase();
        const code = (p.programme_code || "").toLowerCase();
        const desc = (p.description || "").toLowerCase();
        const combined = `${code} ${name} ${desc}`;
        return (
          name.includes(term) ||
          code.includes(term) ||
          desc.includes(term) ||
          combined.includes(term)
        );
      })
    );
  }, [search, programmes]);

  // Helpers
  const resetForm = () => {
    setName("");
    setCode("");
    setNqfLevel("");
    setCredits("");
    setDescription("");
  };

  const cancelEdit = () => {
    setEditingProgrammeId(null);
    resetForm();
    setSaveError("");
    setSaveMessage("");
  };

  // When a row is clicked, populate the form and enter edit mode
  const handleRowClick = (programme) => {
    setEditingProgrammeId(programme.id || null);
    setName(programme.programme_name || "");
    setCode(programme.programme_code || "");
    setNqfLevel(
      programme.nqf_level !== null && programme.nqf_level !== undefined
        ? String(programme.nqf_level)
        : ""
    );
    setCredits(
      programme.credits !== null && programme.credits !== undefined
        ? String(programme.credits)
        : ""
    );
    setDescription(programme.description || "");
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
        ? `${apiBase}/programmes/${editingProgrammeId}`
        : `${apiBase}/programmes`;

      const resp = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          programme_name: name,
          programme_code: code,
          nqf_level: nqfLevel ? Number(nqfLevel) : null,
          credits: credits ? Number(credits) : null,
          description,
        }),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      const returnedProgramme = data.programme;

      if (isEditing) {
        const updated = returnedProgramme || {
          id: editingProgrammeId,
          programme_name: name,
          programme_code: code,
          nqf_level: nqfLevel ? Number(nqfLevel) : null,
          credits: credits ? Number(credits) : null,
          description,
        };

        setProgrammes((prev) =>
          prev.map((p) => (p.id === updated.id ? updated : p))
        );

        // ✅ After successful save, clear inputs and deselect the row
        cancelEdit();

        setSaveMessage("Programme updated successfully.");
      } else {
        const newProg = returnedProgramme || {
          id: data.id,
          programme_name: name,
          programme_code: code,
          nqf_level: nqfLevel ? Number(nqfLevel) : null,
          credits: credits ? Number(credits) : null,
          description,
        };

        setProgrammes((prev) => [...prev, newProg]);
        resetForm();
        setSaveMessage("Programme created successfully.");
      }

      // Auto-hide toast after a few seconds
      setTimeout(() => {
        setSaveMessage("");
      }, 3000);
    } catch (err) {
      console.error("Failed to save programme", err);
      setSaveError(err.message || "Failed to save programme.");
    } finally {
      setSaving(false);
    }
  };

  // Delete handler
  const handleDelete = async (programme) => {
    setDeleteError("");

    const confirmDelete = window.confirm(
      `Delete programme "${programme.programme_name}"?`
    );
    if (!confirmDelete) return;

    try {
      const token = await getTokenForApi();
      const url = `${apiBase}/programmes/${programme.id}`;

      const resp = await fetch(url, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      setProgrammes((prev) => prev.filter((p) => p.id !== programme.id));

      // If we were editing this programme, exit edit mode & clear form
      if (editingProgrammeId === programme.id) {
        cancelEdit();
      }
    } catch (err) {
      console.error("Failed to delete programme", err);
      setDeleteError(err.message || "Failed to delete programme.");
    }
  };

  return (
    <section>
      {/* Header + search, same layout as LearnersPage */}
      <div className="learners-header">
        <div>
          <h1 className="page-title">Programmes</h1>
          <p className="page-subtitle">
            Maintain MICT SETA–aligned learnerships and skills programmes.
          </p>
        </div>

        <div className="learners-search">
          <label htmlFor="programme-search">Search</label>
          <input
            id="programme-search"
            type="text"
            placeholder="Search by code, name, description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Create / Edit card (shared form) */}
      <div className="learners-edit-card">
        <div className="learners-edit-header">
          <div>
            <h2 className="panel-title">
              {isEditing
                ? `Update programme #${editingProgrammeId}`
                : "Create new programme"}
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
              <label htmlFor="prog_name">Programme name</label>
              <input
                id="prog_name"
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              />
            </div>
            <div className="form-field">
              <label htmlFor="prog_code">Code</label>
              <input
                id="prog_code"
                type="text"
                value={code}
                onChange={(e) => {
                  setCode(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="prog_nqf">NQF level</label>
              <input
                id="prog_nqf"
                type="number"
                min="1"
                max="10"
                value={nqfLevel}
                onChange={(e) => {
                  setNqfLevel(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              />
            </div>
            <div className="form-field">
              <label htmlFor="prog_credits">Credits</label>
              <input
                id="prog_credits"
                type="number"
                min="0"
                value={credits}
                onChange={(e) => {
                  setCredits(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="prog_desc">Description</label>
              <textarea
                id="prog_desc"
                rows="3"
                value={description}
                onChange={(e) => {
                  setDescription(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
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
                : "Save programme"}
            </button>
          </div>
        </form>

        {saveError && <div className="message message-error">{saveError}</div>}
      </div>

      {loading && <p>Loading…</p>}

      {loadError && !loading && (
        <div className="message message-error">
          Error loading programmes: {loadError}
        </div>
      )}

      {deleteError && (
        <div className="message message-error">
          Error deleting programme: {deleteError}</div>
      )}

      {!loading && !loadError && filtered.length === 0 && (
        <p>No programmes found.</p>
      )}

      {!loading && !loadError && filtered.length > 0 && (
        <div className="table-wrapper">
          <table className="table learners-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Code</th>
                <th>Name</th>
                <th>NQF</th>
                <th>Credits</th>
                <th style={{ width: "1%", whiteSpace: "nowrap" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr
                  key={p.id}
                  onClick={() => handleRowClick(p)}
                  style={{ cursor: "pointer" }}
                >
                  <td>{p.id}</td>
                  <td>{p.programme_code}</td>
                  <td>{p.programme_name}</td>
                  <td>{p.nqf_level}</td>
                  <td>{p.credits}</td>
                  <td>
                    <div className="table-actions">
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRowClick(p);
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(p);
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

      {/* Save confirmation toast */}
      {saveMessage && <div className="toast toast-success">{saveMessage}</div>}
    </section>
  );
}

export default ProgrammesPage;
