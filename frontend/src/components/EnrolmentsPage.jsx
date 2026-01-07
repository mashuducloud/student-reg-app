// src/components/EnrolmentsPage.jsx
import React, { useEffect, useState } from "react";
import { getTokenForApi } from "../authClient";

function EnrolmentsPage() {
  const [enrolments, setEnrolments] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  // Form / edit state (same pattern as ProgrammesPage)
  const [editingEnrolmentId, setEditingEnrolmentId] = useState(null);
  const [formStudentId, setFormStudentId] = useState("");
  const [formProgrammeId, setFormProgrammeId] = useState("");
  const [formStatus, setFormStatus] = useState("applied");
  const [formEnrolmentDate, setFormEnrolmentDate] = useState("");
  const [formCompletionDate, setFormCompletionDate] = useState("");

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  const [deleteError, setDeleteError] = useState("");

  // Dropdown data
  const [students, setStudents] = useState([]);
  const [programmes, setProgrammes] = useState([]);

  const isEditing = editingEnrolmentId !== null;

  const apiBase =
    window.location.hostname === "localhost"
      ? "http://localhost:5000"
      : "http://student-app:5000";

  // Helper: status label
  const formatStatus = (value) => {
    if (!value) return "";
    const v = String(value).toLowerCase();
    if (v === "applied") return "Applied";
    if (v === "enrolled") return "Enrolled";
    if (v === "completed") return "Completed";
    if (v === "withdrawn") return "Withdrawn";
    // fallback, just capitalise first letter
    return v.charAt(0).toUpperCase() + v.slice(1);
  };

  // ---- Fetch enrolments + students + programmes on mount ----
  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const token = await getTokenForApi();

        const [enrolResp, studResp, progResp] = await Promise.all([
          fetch(`${apiBase}/enrolments`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiBase}/students`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${apiBase}/programmes`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        const [enrolDataRaw, studDataRaw, progDataRaw] = await Promise.all([
          enrolResp.json().catch(() => []),
          studResp.json().catch(() => []),
          progResp.json().catch(() => []),
        ]);

        if (!enrolResp.ok) {
          throw new Error(
            enrolDataRaw.error || `Failed to load enrolments: ${enrolResp.status}`
          );
        }
        if (!studResp.ok) {
          throw new Error(
            studDataRaw.error || `Failed to load students: ${studResp.status}`
          );
        }
        if (!progResp.ok) {
          throw new Error(
            progDataRaw.error || `Failed to load programmes: ${progResp.status}`
          );
        }

        const enrolData = enrolDataRaw || [];
        setEnrolments(enrolData);
        setFiltered(enrolData);

        setStudents(studDataRaw || []);
        setProgrammes(progDataRaw || []);
      } catch (err) {
        console.error("Failed to load enrolments/students/programmes", err);
        setLoadError(
          err.message || "Failed to load enrolments / students / programmes."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [apiBase]);

  // ---- Helpers to derive display strings from enrolment row ----

  const getStudentDisplay = (enrol) => {
    // Try various shapes as defensive programming
    if (enrol.student_full_name) return enrol.student_full_name;
    if (enrol.student_name) return enrol.student_name;

    if (enrol.student && (enrol.student.first_name || enrol.student.last_name)) {
      return `${enrol.student.first_name || ""} ${
        enrol.student.last_name || ""
      }`.trim();
    }

    if (enrol.first_name || enrol.last_name) {
      return `${enrol.first_name || ""} ${enrol.last_name || ""}`.trim();
    }

    const s = students.find((st) => st.id === enrol.student_id);
    if (s) {
      return `${s.first_name || ""} ${s.last_name || ""}`.trim();
    }

    return `Student #${enrol.student_id}`;
  };

  const getStudentEmail = (enrol) => {
    if (enrol.student_email) return enrol.student_email;
    if (enrol.student && enrol.student.email) return enrol.student.email;
    if (enrol.email) return enrol.email;

    const s = students.find((st) => st.id === enrol.student_id);
    return s?.email || "";
  };

  const getProgrammeDisplay = (enrol) => {
    if (enrol.programme_name && enrol.programme_code) {
      return `${enrol.programme_code} – ${enrol.programme_name}`;
    }
    if (enrol.programme_name) return enrol.programme_name;
    if (enrol.programme_code) return enrol.programme_code;

    if (
      enrol.programme &&
      (enrol.programme.programme_name || enrol.programme.programme_code)
    ) {
      const p = enrol.programme;
      if (p.programme_name && p.programme_code) {
        return `${p.programme_code} – ${p.programme_name}`;
      }
      return p.programme_name || p.programme_code;
    }

    const p = programmes.find((pr) => pr.id === enrol.programme_id);
    if (p) {
      if (p.programme_code && p.programme_name) {
        return `${p.programme_code} – ${p.programme_name}`;
      }
      return p.programme_name || p.programme_code;
    }

    return `Programme #${enrol.programme_id}`;
  };

  // ---- Client-side search (same idea as ProgrammesPage) ----
  useEffect(() => {
    const term = search.toLowerCase().trim();
    if (!term) {
      setFiltered(enrolments);
      return;
    }

    setFiltered(
      enrolments.filter((e) => {
        const studentName = getStudentDisplay(e).toLowerCase();
        const studentEmail = getStudentEmail(e).toLowerCase();
        const programme = getProgrammeDisplay(e).toLowerCase();
        const status = formatStatus(e.enrolment_status).toLowerCase();
        const idStr = String(e.id || "");

        const combined = `${studentName} ${studentEmail} ${programme} ${status} ${idStr}`;

        return (
          studentName.includes(term) ||
          studentEmail.includes(term) ||
          programme.includes(term) ||
          status.includes(term) ||
          idStr.includes(term) ||
          combined.includes(term)
        );
      })
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, enrolments, students, programmes]);

  // ---- Helpers: reset / cancel ----
  const resetForm = () => {
    setFormStudentId("");
    setFormProgrammeId("");
    setFormStatus("applied");
    setFormEnrolmentDate("");
    setFormCompletionDate("");
  };

  const cancelEdit = () => {
    setEditingEnrolmentId(null);
    resetForm();
    setSaveError("");
    setSaveMessage("");
  };

  // ---- Row click → edit mode (same UX as ProgrammesPage) ----
  const handleRowClick = (enrol) => {
    setEditingEnrolmentId(enrol.id || null);
    setFormStudentId(
      enrol.student_id !== null && enrol.student_id !== undefined
        ? String(enrol.student_id)
        : ""
    );
    setFormProgrammeId(
      enrol.programme_id !== null && enrol.programme_id !== undefined
        ? String(enrol.programme_id)
        : ""
    );
    setFormStatus(enrol.enrolment_status || "applied");
    setFormEnrolmentDate(enrol.enrolment_date || "");
    setFormCompletionDate(enrol.completion_date || "");
    setSaveError("");
    setSaveMessage("");
  };

  // ---- Create / Update submit handler ----
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaveError("");
    setSaveMessage("");
    setDeleteError("");
    setSaving(true);

    try {
      if (!formStudentId || !formProgrammeId) {
        throw new Error("Please select a learner and a programme.");
      }

      const token = await getTokenForApi();
      const url = isEditing
        ? `${apiBase}/enrolments/${editingEnrolmentId}`
        : `${apiBase}/enrolments`;

      const payload = {
        student_id: Number(formStudentId),
        programme_id: Number(formProgrammeId),
        enrolment_status: formStatus || "applied",
        enrolment_date: formEnrolmentDate || null,
        completion_date: formCompletionDate || null,
      };

      const resp = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      const returned = data.enrolment || {
        id: isEditing ? editingEnrolmentId : data.id,
        ...payload,
      };

      if (isEditing) {
        setEnrolments((prev) =>
          prev.map((eRow) => (eRow.id === returned.id ? returned : eRow))
        );
        cancelEdit();
        setSaveMessage("Enrolment updated successfully.");
      } else {
        setEnrolments((prev) => [...prev, returned]);
        resetForm();
        setSaveMessage("Enrolment created successfully.");
      }

      setTimeout(() => {
        setSaveMessage("");
      }, 3000);
    } catch (err) {
      console.error("Failed to save enrolment", err);
      setSaveError(err.message || "Failed to save enrolment.");
    } finally {
      setSaving(false);
    }
  };

  // ---- Delete handler ----
  const handleDelete = async (enrol) => {
    setDeleteError("");

    const confirmDelete = window.confirm(
      `Delete enrolment #${enrol.id} for ${getStudentDisplay(
        enrol
      )} on ${getProgrammeDisplay(enrol)}?`
    );
    if (!confirmDelete) return;

    try {
      const token = await getTokenForApi();
      const url = `${apiBase}/enrolments/${enrol.id}`;

      const resp = await fetch(url, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      setEnrolments((prev) => prev.filter((eRow) => eRow.id !== enrol.id));

      if (editingEnrolmentId === enrol.id) {
        cancelEdit();
      }
    } catch (err) {
      console.error("Failed to delete enrolment", err);
      setDeleteError(err.message || "Failed to delete enrolment.");
    }
  };

  return (
    <section>
      {/* Header + search – same layout classes as Learners/Programmes */}
      <div className="learners-header">
        <div>
          <h1 className="page-title">Enrolments</h1>
          <p className="page-subtitle">
            Link learners to programmes and track enrolment status.
          </p>
        </div>

        <div className="learners-search">
          <label htmlFor="enrolment-search">Search</label>
          <input
            id="enrolment-search"
            type="text"
            placeholder="Search by learner, programme, status..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Create / Edit card – mirrors ProgrammesPage layout */}
      <div className="learners-edit-card">
        <div className="learners-edit-header">
          <div>
            <h2 className="panel-title">
              {isEditing
                ? `Update enrolment #${editingEnrolmentId}`
                : "Create new enrolment"}
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
              <label htmlFor="enrol_student">Learner</label>
              <select
                id="enrol_student"
                value={formStudentId}
                onChange={(e) => {
                  setFormStudentId(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              >
                <option value="">Select learner...</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {`${s.first_name || ""} ${s.last_name || ""}`.trim()}{" "}
                    {s.email ? `(${s.email})` : ""}
                  </option>
                ))}
              </select>
              <small>Select the learner to enrol.</small>
            </div>

            <div className="form-field">
              <label htmlFor="enrol_programme">Programme</label>
              <select
                id="enrol_programme"
                value={formProgrammeId}
                onChange={(e) => {
                  setFormProgrammeId(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              >
                <option value="">Select programme...</option>
                {programmes.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.programme_code
                      ? `${p.programme_code} – ${p.programme_name}`
                      : p.programme_name || `Programme #${p.id}`}
                  </option>
                ))}
              </select>
              <small>Choose the learnership / skills programme.</small>
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="enrol_status">Status</label>
              <select
                id="enrol_status"
                value={formStatus}
                onChange={(e) => {
                  setFormStatus(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              >
                <option value="applied">Applied</option>
                <option value="enrolled">Enrolled</option>
                <option value="completed">Completed</option>
                <option value="withdrawn">Withdrawn</option>
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="enrol_date">Enrolment date</label>
              <input
                id="enrol_date"
                type="date"
                value={formEnrolmentDate}
                onChange={(e) => {
                  setFormEnrolmentDate(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              />
            </div>

            <div className="form-field">
              <label htmlFor="complete_date">Completion date</label>
              <input
                id="complete_date"
                type="date"
                value={formCompletionDate}
                onChange={(e) => {
                  setFormCompletionDate(e.target.value);
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
                ? "Saving..."
                : isEditing
                ? "Save changes"
                : "Save enrolment"}
            </button>
          </div>
        </form>

        {saveError && <div className="message message-error">{saveError}</div>}
      </div>

      {loading && <p>Loading…</p>}

      {loadError && !loading && (
        <div className="message message-error">
          Error loading enrolments: {loadError}
        </div>
      )}

      {deleteError && (
        <div className="message message-error">
          Error deleting enrolment: {deleteError}
        </div>
      )}

      {!loading && !loadError && filtered.length === 0 && (
        <p>No enrolments found.</p>
      )}

      {!loading && !loadError && filtered.length > 0 && (
        <div className="table-wrapper">
          <table className="table learners-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Learner</th>
                <th>Email</th>
                <th>Programme</th>
                <th>Status</th>
                <th>Enrolment date</th>
                <th>Completion date</th>
                <th style={{ width: "1%", whiteSpace: "nowrap" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => {
                const studentName = getStudentDisplay(e);
                const studentEmail = getStudentEmail(e);
                const programme = getProgrammeDisplay(e);

                return (
                  <tr
                    key={e.id}
                    onClick={() => handleRowClick(e)}
                    className={
                      editingEnrolmentId === e.id
                        ? "table-row-editing"
                        : undefined
                    }
                    style={{ cursor: "pointer" }}
                  >
                    <td>{e.id}</td>
                    <td>{studentName}</td>
                    <td>{studentEmail}</td>
                    <td>{programme}</td>
                    <td>{formatStatus(e.enrolment_status)}</td>
                    <td>{e.enrolment_date || ""}</td>
                    <td>{e.completion_date || ""}</td>
                    <td>
                      <div
                        className="table-actions"
                        onClick={(ev) => ev.stopPropagation()}
                      >
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleRowClick(e)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDelete(e)}
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Save confirmation toast – same pattern as ProgrammesPage */}
      {saveMessage && <div className="toast toast-success">{saveMessage}</div>}
    </section>
  );
}

export default EnrolmentsPage;
