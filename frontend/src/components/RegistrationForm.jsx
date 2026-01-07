// src/components/RegistrationForm.jsx
import React, { useState } from "react";
import { getTokenForApi } from "../authClient";

function RegistrationForm({ onLogout }) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setIsError(false);

    const studentData = {
      first_name: firstName,
      last_name: lastName,
      email: email,
    };

    let token;
    try {
      // Get token for already-signed-in user
      token = await getTokenForApi();
    } catch (err) {
      setLoading(false);
      const msg = err?.message || "";
      if (msg.includes("No signed-in user")) {
        setMessage("Please sign in on the Admin Login page first.");
      } else if (
        (err?.errorCode || "").includes("user_cancelled") ||
        (err?.error || "").includes("user_cancelled")
      ) {
        setMessage("Authorization was cancelled. Please try again.");
      } else {
        setMessage(`Failed to get access token: ${msg}`);
      }
      setIsError(true);
      return;
    }

    try {
      const apiUrl =
        window.location.hostname === "localhost"
          ? "http://localhost:5000/register"
          : "http://student-app:5000/register";

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(studentData),
      });

      const result = await response.json();

      if (response.ok) {
        setMessage(result.message || "Student registered successfully");
        setIsError(false);
        setFirstName("");
        setLastName("");
        setEmail("");
      } else {
        throw new Error(result.error || "An unknown error occurred.");
      }
    } catch (err) {
      setMessage(`Error: ${err.message}`);
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Local header for the form section */}
      <div className="form-header-row">
        <div>
          <p className="badge">Admin Panel</p>
          <h2 className="panel-title">Student Registration</h2>
          <p className="page-subtitle">
            Fill out the form below to register a new student.
          </p>
        </div>

        <button
          onClick={onLogout}
          className="btn btn-secondary"
          type="button"
        >
          Logout
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Row 1: first / last name */}
        <div className="form-row">
          <div className="form-field">
            <label htmlFor="first_name">First Name</label>
            <input
              type="text"
              id="first_name"
              placeholder="e.g., John"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="last_name">Last Name</label>
            <input
              type="text"
              id="last_name"
              placeholder="e.g., Doe"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
          </div>
        </div>

        {/* Row 2: email */}
        <div className="form-row">
          <div className="form-field">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              placeholder="e.g., john.doe@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
        </div>

        {/* Actions: right-aligned Register button */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? "Registering..." : "Register Student"}
          </button>
        </div>
      </form>

      {message && (
        <div
          className={
            "message " + (isError ? "message-error" : "")
          }
        >
          {message}
        </div>
      )}
    </>
  );
}

export default RegistrationForm;
