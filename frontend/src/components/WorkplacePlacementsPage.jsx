// src/components/WorkplacePlacementsPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { getTokenForApi } from "../authClient";

function WorkplacePlacementsPage() {
  const [placements, setPlacements] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState("");

  const [learners, setLearners] = useState([]);

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  // Form / edit state
  const [editingPlacementId, setEditingPlacementId] = useState(null);
  const [formStudentId, setFormStudentId] = useState("");
  const [formEmployerName, setFormEmployerName] = useState("");
  const [formEmployerContact, setFormEmployerContact] = useState("");
  const [formSupervisorName, setFormSupervisorName] = useState("");
  const [formSupervisorPhone, setFormSupervisorPhone] = useState("");
  const [formStartDate, setFormStartDate] = useState("");
  const [formEndDate, setFormEndDate] = useState("");

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  const [deleteError, setDeleteError] = useState("");

  const isEditing = editingPlacementId !== null;

  const apiBase =
    window.location.hostname === "localhost"
      ? "http://localhost:5000"
      : "http://student-app:5000";

  // Build a quick lookup map: student_id -> {id, first_name, last_name}
  const learnerById = useMemo(() => {
    const map = new Map();
    learners.forEach((l) => {
      map.set(l.id, l);
    });
    return map;
  }, [learners]);

  const learnerLabel = (studentId) => {
    if (!studentId) return "";
    const learner = learnerById.get(studentId);
    if (!learner) return `${studentId}`;
    const fn = learner.first_name || "";
    const ln = learner.last_name || "";
    return `${studentId} – ${fn} ${ln}`.trim();
  };

  // Fetch placements + learners
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const token = await getTokenForApi();

        const [placementsResp, learnersResp] = await Promise.all([
          fetch(`${apiBase}/workplace-placements`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiBase}/students`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        if (!placementsResp.ok) {
          const data = await placementsResp.json().catch(() => ({}));
          throw new Error(data.error || `Failed placements: ${placementsResp.status}`);
        }

        if (!learnersResp.ok) {
          const data = await learnersResp.json().catch(() => ({}));
          throw new Error(data.error || `Failed learners: ${learnersResp.status}`);
        }

        const placementsData = await placementsResp.json();
        const learnersData = await learnersResp.json();

        setPlacements(placementsData || []);
        setFiltered(placementsData || []);
        setLearners(learnersData || []);
      } catch (err) {
        console.error("Failed to load workplace placements", err);
        setLoadError(err.message || "Failed to load workplace placements");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Search across employer, supervisor, and learner (id/name)
  useEffect(() => {
    const term = search.toLowerCase().trim();
    if (!term) {
      setFiltered(placements);
      return;
    }

    setFiltered(
      placements.filter((p) => {
        const employer = (p.employer_name || "").toLowerCase();
        const contact = (p.employer_contact || "").toLowerCase();
        const supName = (p.supervisor_name || "").toLowerCase();
        const supPhone = (p.supervisor_phone || "").toLowerCase();

        const learner = learnerById.get(p.student_id);
        const learnerIdString = p.student_id != null ? String(p.student_id) : "";
        const learnerFirst = learner ? (learner.first_name || "").toLowerCase() : "";
        const learnerLast = learner ? (learner.last_name || "").toLowerCase() : "";
        const learnerFull = `${learnerFirst} ${learnerLast}`.trim();

        return (
          employer.includes(term) ||
          contact.includes(term) ||
          supName.includes(term) ||
          supPhone.includes(term) ||
          learnerIdString.includes(term) ||
          learnerFirst.includes(term) ||
          learnerLast.includes(term) ||
          learnerFull.includes(term)
        );
      })
    );
  }, [search, placements, learnerById]);

  const resetForm = () => {
    setFormStudentId("");
    setFormEmployerName("");
    setFormEmployerContact("");
    setFormSupervisorName("");
    setFormSupervisorPhone("");
    setFormStartDate("");
    setFormEndDate("");
  };

  const cancelEdit = () => {
    setEditingPlacementId(null);
    resetForm();
    setSaveError("");
    setSaveMessage("");
  };

  // Row click → populate form
  const handleRowClick = (placement) => {
    setEditingPlacementId(placement.id || null);
    setFormStudentId(
      placement.student_id !== null && placement.student_id !== undefined
        ? String(placement.student_id)
        : ""
    );
    setFormEmployerName(placement.employer_name || "");
    setFormEmployerContact(placement.employer_contact || "");
    setFormSupervisorName(placement.supervisor_name || "");
    setFormSupervisorPhone(placement.supervisor_phone || "");
    setFormStartDate(placement.start_date || "");
    setFormEndDate(placement.end_date || "");
    setSaveError("");
    setSaveMessage("");
  };

  // Create / update submit handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaveError("");
    setSaveMessage("");
    setDeleteError("");
    setSaving(true);

    const studentIdNum = formStudentId ? Number(formStudentId) : null;

    if (!studentIdNum || !formEmployerName.trim()) {
      setSaving(false);
      setSaveError("Learner and employer name are required.");
      return;
    }

    try {
      const token = await getTokenForApi();
      const url = isEditing
        ? `${apiBase}/workplace-placements/${editingPlacementId}`
        : `${apiBase}/workplace-placements`;

      const resp = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          student_id: studentIdNum,
          employer_name: formEmployerName.trim(),
          employer_contact: formEmployerContact.trim() || null,
          supervisor_name: formSupervisorName.trim() || null,
          supervisor_phone: formSupervisorPhone.trim() || null,
          start_date: formStartDate || null,
          end_date: formEndDate || null,
        }),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      const returned = data.placement || {
        id: data.id || editingPlacementId,
        student_id: studentIdNum,
        employer_name: formEmployerName.trim(),
        employer_contact: formEmployerContact.trim() || null,
        supervisor_name: formSupervisorName.trim() || null,
        supervisor_phone: formSupervisorPhone.trim() || null,
        start_date: formStartDate || null,
        end_date: formEndDate || null,
      };

      if (isEditing) {
        setPlacements((prev) =>
          prev.map((p) => (p.id === returned.id ? returned : p))
        );
        cancelEdit();
        setSaveMessage("Placement updated successfully.");
      } else {
        setPlacements((prev) => [...prev, returned]);
        resetForm();
        setSaveMessage("Placement created successfully.");
      }

      setTimeout(() => setSaveMessage(""), 3000);
    } catch (err) {
      console.error("Failed to save workplace placement", err);
      setSaveError(err.message || "Failed to save workplace placement.");
    } finally {
      setSaving(false);
    }
  };

  // Delete handler
  const handleDelete = async (placement) => {
    setDeleteError("");

    const confirmDelete = window.confirm(
      `Delete placement for learner "${learnerLabel(placement.student_id)}" at "${placement.employer_name}"?`
    );
    if (!confirmDelete) return;

    try {
      const token = await getTokenForApi();
      const url = `${apiBase}/workplace-placements/${placement.id}`;

      const resp = await fetch(url, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      setPlacements((prev) => prev.filter((p) => p.id !== placement.id));

      if (editingPlacementId === placement.id) {
        cancelEdit();
      }
    } catch (err) {
      console.error("Failed to delete workplace placement", err);
      setDeleteError(err.message || "Failed to delete workplace placement.");
    }
  };

  return (
    <section>
      {/* Header + search, same layout as ProgrammesPage/LearnersPage */}
      <div className="learners-header">
        <div>
          <h1 className="page-title">Workplace placements</h1>
          <p className="page-subtitle">
            Link learners to employers and track start / end dates.
          </p>
        </div>

        <div className="learners-search">
          <label htmlFor="placement-search">Search</label>
          <input
            id="placement-search"
            type="text"
            placeholder="Search by learner, employer or supervisor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Create / Edit card */}
      <div className="learners-edit-card">
        <div className="learners-edit-header">
          <div>
            <h2 className="panel-title">
              {isEditing
                ? `Update placement #${editingPlacementId}`
                : "Create new placement"}
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
              <label htmlFor="placement_student">Learner</label>
              <select
                id="placement_student"
                value={formStudentId}
                onChange={(e) => {
                  setFormStudentId(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              >
                <option value="">Select learner…</option>
                {learners.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.id} – {l.first_name} {l.last_name}
                  </option>
                ))}
              </select>
              <small>Displayed as learner ID, first name and surname.</small>
            </div>

            <div className="form-field">
              <label htmlFor="employer_name">Employer name</label>
              <input
                id="employer_name"
                type="text"
                value={formEmployerName}
                onChange={(e) => {
                  setFormEmployerName(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="employer_contact">Employer contact</label>
              <input
                id="employer_contact"
                type="text"
                value={formEmployerContact}
                onChange={(e) => {
                  setFormEmployerContact(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              />
              <small>Contact person or generic email / phone.</small>
            </div>

            <div className="form-field">
              <label htmlFor="supervisor_name">Supervisor name</label>
              <input
                id="supervisor_name"
                type="text"
                value={formSupervisorName}
                onChange={(e) => {
                  setFormSupervisorName(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="supervisor_phone">Supervisor phone</label>
              <input
                id="supervisor_phone"
                type="text"
                value={formSupervisorPhone}
                onChange={(e) => {
                  setFormSupervisorPhone(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              />
            </div>

            <div className="form-field">
              <label htmlFor="start_date">Start date</label>
              <input
                id="start_date"
                type="date"
                value={formStartDate}
                onChange={(e) => {
                  setFormStartDate(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              />
            </div>

            <div className="form-field">
              <label htmlFor="end_date">End date</label>
              <input
                id="end_date"
                type="date"
                value={formEndDate}
                onChange={(e) => {
                  setFormEndDate(e.target.value);
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
                : "Save placement"}
            </button>
          </div>
        </form>

        {saveError && <div className="message message-error">{saveError}</div>}
      </div>

      {loading && <p>Loading…</p>}

      {loadError && !loading && (
        <div className="message message-error">
          Error loading placements: {loadError}
        </div>
      )}

      {deleteError && (
        <div className="message message-error">
          Error deleting placement: {deleteError}
        </div>
      )}

      {!loading && !loadError && filtered.length === 0 && (
        <p>No workplace placements found.</p>
      )}

      {!loading && !loadError && filtered.length > 0 && (
        <div className="table-wrapper">
          <table className="table learners-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Learner</th>
                <th>Employer</th>
                <th>Supervisor</th>
                <th>Start</th>
                <th>End</th>
                <th style={{ width: "1%", whiteSpace: "nowrap" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr
                  key={p.id}
                  onClick={() => handleRowClick(p)}
                  style={{ cursor: "pointer" }}
                  className={
                    editingPlacementId === p.id ? "table-row-editing" : undefined
                  }
                >
                  <td>{p.id}</td>
                  <td>{learnerLabel(p.student_id)}</td>
                  <td>{p.employer_name}</td>
                  <td>{p.supervisor_name}</td>
                  <td>{p.start_date}</td>
                  <td>{p.end_date}</td>
                  <td>
                    <div
                      className="table-actions"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleRowClick(p)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(p)}
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

      {saveMessage && (
        <div className="toast toast-success">{saveMessage}</div>
      )}
    </section>
  );
}

export default WorkplacePlacementsPage;
