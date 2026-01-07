// src/components/LoginForm.jsx
import React, { useState } from "react";
import { loginWithPopup } from "../authClient";

function LoginForm({ onLogin }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // MSAL popup login – same as before
      const account = await loginWithPopup();

      // Safely get claims from the ID token
      const claims = (account && account.idTokenClaims) || {};

      // Try roles first, then groups, then any custom extension
      const rawRoles =
        claims.roles ||
        claims.groups ||
        claims.appRoles ||
        claims["extension_appRoles"] ||
        [];

      const roles = Array.isArray(rawRoles) ? rawRoles : [rawRoles].filter(Boolean);
      console.log("🔐 ID token roles:", roles);

      // Pass account + roles back to App
      onLogin({
        account,
        roles,
      });
    } catch (err) {
      console.error("Login failed", err);
      const code = err?.errorCode || err?.error || "";
      if (typeof code === "string" && code.includes("user_cancelled")) {
        setError("Sign-in was cancelled. Please try again.");
      } else {
        setError(
          "Failed to sign in. " + (err?.message || "Please check your account.")
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="title">MICT Learner Management</h1>
      <p className="subtitle">
        Sign in with your Microsoft (Entra ID) account to continue.
      </p>

      <form onSubmit={handleSubmit}>
        <button type="submit" className="button" disabled={loading}>
          {loading ? "Signing in..." : "Sign in with Microsoft"}
        </button>
      </form>

      {error && <div className="message message-error">{error}</div>}
    </>
  );
}

export default LoginForm;
