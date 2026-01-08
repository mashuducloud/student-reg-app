// src/components/AssessmentsPage.jsx
import React, { useEffect, useState } from "react";
import { getTokenForApi } from "../authClient";

function AssessmentsPage() {
  const [assessments, setAssessments] = useState([]);
  const [students, setStudents] = useState([]);
  const [programmes, setProgrammes] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [editingId, setEditingId] = useState(null);
  const [formStudentId, setFormStudentId] = useState("");
  const [formProgrammeId, setFormProgrammeId] = useState("");
  const [formAssessmentType, setFormAssessmentType] = useState("formative");
  const [formAssessmentName, setFormAssessmentName] = useState("");
  const [formAssessmentDate, setFormAssessmentDate] = useState("");
  const [formScore, setFormScore] = useState("");
  const [formMaxScore, setFormMaxScore] = useState("");
  const [formResult, setFormResult] = useState("");
  const [formModerationOutcome, setFormModerationOutcome] = useState("");

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  const [deleteError, setDeleteError] = useState("");

  const apiBase =
    window.location.hostname === "localhost"
      ? "http://localhost:5000"
      : "http://student-app:5000";

  const isEditing = editingId !== null;

  // Helpers to show nicer labels
  const learnerLabel = (studentId) => {
    if (!studentId) return "";
    const s = students.find((st) => st.id === Number(studentId));
    if (!s) return String(studentId);
    return `${s.id} – ${s.first_name} ${s.last_name}`;
  };

  const programmeLabel = (programmeId) => {
    if (!programmeId) return "";
    const p = programmes.find((pr) => pr.id === Number(programmeId));
    if (!p) return String(programmeId);
    return `${p.programme_code || p.id} – ${p.programme_name}`;
  };

  // Load students, programmes, assessments once
  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const token = await getTokenForApi();

        const [studentsResp, programmesResp, assessmentsResp] =
          await Promise.all([
            fetch(`${apiBase}/students`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
            fetch(`${apiBase}/programmes`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
            fetch(`${apiBase}/assessments`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
          ]);

        if (!studentsResp.ok) {
          const data = await studentsResp.json().catch(() => ({}));
          throw new Error(data.error || "Failed to load students");
        }
        if (!programmesResp.ok) {
          const data = await programmesResp.json().catch(() => ({}));
          throw new Error(data.error || "Failed to load programmes");
        }
        if (!assessmentsResp.ok) {
          const data = await assessmentsResp.json().catch(() => ({}));
          throw new Error(data.error || "Failed to load assessments");
        }

        const studentsData = await studentsResp.json();
        const programmesData = await programmesResp.json();
        const assessmentsData = await assessmentsResp.json();

        setStudents(studentsData || []);
        setProgrammes(programmesData || []);
        setAssessments(assessmentsData || []);
        setFiltered(assessmentsData || []);
      } catch (err) {
        console.error("Failed to load assessments", err);
        setLoadError(err.message || "Failed to load assessments");
      } finally {
        setLoading(false);
      }
    };

    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Search filter
  useEffect(() => {
    const term = search.toLowerCase().trim();
    if (!term) {
      setFiltered(assessments);
      return;
    }

    setFiltered(
      assessments.filter((a) => {
        const learner = learnerLabel(a.student_id).toLowerCase();
        const programme = programmeLabel(a.programme_id).toLowerCase();
        const name = (a.assessment_name || "").toLowerCase();
        const type = (a.assessment_type || "").toLowerCase();
        const result = (a.result || "").toLowerCase();
        const moderation = (a.moderation_outcome || "").toLowerCase();
        const combined = `${learner} ${programme} ${name} ${type} ${result} ${moderation}`;

        return (
          learner.includes(term) ||
          programme.includes(term) ||
          name.includes(term) ||
          type.includes(term) ||
          result.includes(term) ||
          moderation.includes(term) ||
          combined.includes(term)
        );
      })
    );
  }, [search, assessments, students, programmes]);

  const resetForm = () => {
    setEditingId(null);
    setFormStudentId("");
    setFormProgrammeId("");
    setFormAssessmentType("formative");
    setFormAssessmentName("");
    setFormAssessmentDate("");
    setFormScore("");
    setFormMaxScore("");
    setFormResult("");
    setFormModerationOutcome("");
    setSaveError("");
    setSaveMessage("");
  };

  const handleRowClick = (assessment) => {
    setEditingId(assessment.id || null);
    setFormStudentId(assessment.student_id ?? "");
    setFormProgrammeId(assessment.programme_id ?? "");
    setFormAssessmentType(assessment.assessment_type || "formative");
    setFormAssessmentName(assessment.assessment_name || "");
    setFormAssessmentDate(assessment.assessment_date || "");
    setFormScore(
      assessment.score !== null && assessment.score !== undefined
        ? String(assessment.score)
        : ""
    );
    setFormMaxScore(
      assessment.max_score !== null && assessment.max_score !== undefined
        ? String(assessment.max_score)
        : ""
    );
    setFormResult(assessment.result || "");
    setFormModerationOutcome(assessment.moderation_outcome || "");
    setSaveError("");
    setSaveMessage("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveError("");
    setSaveMessage("");
    setDeleteError("");

    if (!formStudentId || !formProgrammeId || !formAssessmentName) {
      setSaving(false);
      setSaveError(
        "Learner, Programme and Assessment name are required."
      );
      return;
    }

    const payload = {
      student_id: Number(formStudentId),
      programme_id: Number(formProgrammeId),
      assessment_type: formAssessmentType,
      assessment_name: formAssessmentName,
      assessment_date: formAssessmentDate || null,
      score:
        formScore === "" || formScore === null ? null : Number(formScore),
      max_score:
        formMaxScore === "" || formMaxScore === null
          ? null
          : Number(formMaxScore),
      result: formResult || null,
      moderation_outcome: formModerationOutcome || null,
    };

    const isEdit = !!editingId;
    const url = isEdit
      ? `${apiBase}/assessments/${editingId}`
      : `${apiBase}/assessments`;
    const method = isEdit ? "PUT" : "POST";

    try {
      const token = await getTokenForApi();
      const resp = await fetch(url, {
        method,
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

      // After save, either refetch or update in-place.
      if (isEdit) {
        const updated =
          data.assessment ||
          {
            id: editingId,
            ...payload,
          };

        setAssessments((prev) =>
          prev.map((a) => (a.id === updated.id ? updated : a))
        );
        setSaveMessage("Assessment updated successfully.");
      } else {
        const created =
          data.assessment ||
          {
            id: data.id,
            ...payload,
          };

        setAssessments((prev) => [...prev, created]);
        setSaveMessage("Assessment created successfully.");
      }

      resetForm();

      setTimeout(() => {
        setSaveMessage("");
      }, 3000);
    } catch (err) {
      console.error("Failed to save assessment", err);
      setSaveError(err.message || "Failed to save assessment.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (assessment) => {
    setDeleteError("");

    const confirmDelete = window.confirm(
      `Delete assessment "${assessment.assessment_name}" for learner ${learnerLabel(
        assessment.student_id
      )}?`
    );
    if (!confirmDelete) return;

    try {
      const token = await getTokenForApi();
      const resp = await fetch(`${apiBase}/assessments/${assessment.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        throw new Error(data.error || `Failed: ${resp.status}`);
      }

      setAssessments((prev) => prev.filter((a) => a.id !== assessment.id));

      if (editingId === assessment.id) {
        resetForm();
      }
    } catch (err) {
      console.error("Failed to delete assessment", err);
      setDeleteError(err.message || "Failed to delete assessment.");
    }
  };

  return (
    <section>
      {/* Header + search, same layout pattern as Learners/Programmes */}
      <div className="learners-header">
        <div>
          <h1 className="page-title">Assessments &amp; moderations</h1>
          <p className="page-subtitle">
            Capture formative / summative results and moderation outcomes.
          </p>
        </div>

        <div className="learners-search">
          <label htmlFor="assessment-search">Search</label>
          <input
            id="assessment-search"
            type="text"
            placeholder="Search by learner, programme, type, result..."
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
                ? `Update assessment #${editingId}`
                : "Capture new assessment"}
            </h2>
            <span className="badge">
              {isEditing ? "Edit mode" : "Create mode"}
            </span>
          </div>

          {isEditing && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={resetForm}
            >
              Cancel
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-field">
              <label htmlFor="student_id">Learner</label>
              <select
                id="student_id"
                value={formStudentId}
                onChange={(e) => {
                  setFormStudentId(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              >
                <option value="">Select learner…</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {`${s.id} – ${s.first_name} ${s.last_name}`}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="programme_id">Programme</label>
              <select
                id="programme_id"
                value={formProgrammeId}
                onChange={(e) => {
                  setFormProgrammeId(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                required
              >
                <option value="">Select programme…</option>
                {programmes.map((p) => (
                  <option key={p.id} value={p.id}>
                    {`${p.programme_code || p.id} – ${p.programme_name}`}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="assessment_type">Assessment type</label>
              <select
                id="assessment_type"
                value={formAssessmentType}
                onChange={(e) => {
                  setFormAssessmentType(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              >
                <option value="formative">Formative</option>
                <option value="summative">Summative</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="assessment_name">Assessment name</label>
              <input
                id="assessment_name"
                type="text"
                value={formAssessmentName}
                onChange={(e) => {
                  setFormAssessmentName(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                placeholder="e.g. Assignment 1, Final Summative"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="assessment_date">Assessment date</label>
              <input
                id="assessment_date"
                type="date"
                value={formAssessmentDate}
                onChange={(e) => {
                  setFormAssessmentDate(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              />
            </div>

            <div className="form-field">
              <label htmlFor="score">Score</label>
              <input
                id="score"
                type="number"
                step="0.01"
                value={formScore}
                onChange={(e) => {
                  setFormScore(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                placeholder="e.g. 75"
              />
            </div>

            <div className="form-field">
              <label htmlFor="max_score">Max score</label>
              <input
                id="max_score"
                type="number"
                step="0.01"
                value={formMaxScore}
                onChange={(e) => {
                  setFormMaxScore(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
                placeholder="e.g. 100"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="result">Result</label>
              <select
                id="result"
                value={formResult}
                onChange={(e) => {
                  setFormResult(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              >
                <option value="">Select result…</option>
                <option value="Competent">Competent</option>
                <option value="Not Yet Competent">Not Yet Competent</option>
                <option value="Pending">Pending</option>
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="moderation_outcome">Moderation outcome</label>
              <select
                id="moderation_outcome"
                value={formModerationOutcome}
                onChange={(e) => {
                  setFormModerationOutcome(e.target.value);
                  setSaveError("");
                  setSaveMessage("");
                }}
              >
                <option value="">Not yet moderated</option>
                <option value="Pending">Pending</option>
                <option value="Confirmed">Confirmed</option>
                <option value="Referred back">Referred back</option>
              </select>
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
                : "Create assessment"}
            </button>
          </div>
        </form>

        {saveError && <div className="message message-error">{saveError}</div>}
      </div>

      {loading && <p>Loading…</p>}

      {loadError && !loading && (
        <div className="message message-error">
          Error loading assessments: {loadError}
        </div>
      )}

      {deleteError && (
        <div className="message message-error">
          Error deleting assessment: {deleteError}
        </div>
      )}

      {!loading && !loadError && filtered.length === 0 && (
        <p>No assessments found.</p>
      )}

      {!loading && !loadError && filtered.length > 0 && (
        <div className="table-wrapper">
          <table className="table learners-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Learner</th>
                <th>Programme</th>
                <th>Type</th>
                <th>Assessment</th>
                <th>Date</th>
                <th>Score</th>
                <th>Result</th>
                <th>Moderation</th>
                <th style={{ width: "1%", whiteSpace: "nowrap" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr
                  key={a.id}
                  onClick={() => handleRowClick(a)}
                  style={{ cursor: "pointer" }}
                >
                  <td>{a.id}</td>
                  <td>{learnerLabel(a.student_id)}</td>
                  <td>{programmeLabel(a.programme_id)}</td>
                  <td>{a.assessment_type}</td>
                  <td>{a.assessment_name}</td>
                  <td>{a.assessment_date || ""}</td>
                  <td>
                    {a.score != null && a.max_score != null
                      ? `${a.score} / ${a.max_score}`
                      : ""}
                  </td>
                  <td>{a.result || ""}</td>
                  <td>{a.moderation_outcome || ""}</td>
                  <td>
                    <div
                      className="table-actions"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleRowClick(a)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(a)}
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

export default AssessmentsPage;
