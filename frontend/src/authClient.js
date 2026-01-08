// src/authClient.js
import {
  PublicClientApplication,
  InteractionRequiredAuthError,
} from "@azure/msal-browser";
import { msalConfig, loginRequest } from "./authConfig";

// Single MSAL instance for the whole app
export const msalInstance = new PublicClientApplication(msalConfig);

// Ensure MSAL is initialized before use
let msalInitializationPromise = null;

async function ensureInitialized() {
  if (!msalInitializationPromise) {
    msalInitializationPromise = msalInstance.initialize();
  }
  await msalInitializationPromise;
}

// 🔍 Small helper to decode JWT payload (for debugging/tracing in browser)
function decodeJwt(token) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) {
      return null;
    }
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    // Don't break anything if decode fails; just log in dev tools
    console.warn("Failed to decode JWT", e);
    return null;
  }
}

// Called from the login screen – interactive sign-in
export async function loginWithPopup() {
  await ensureInitialized();

  const loginResponse = await msalInstance.loginPopup(loginRequest);

  if (loginResponse?.account) {
    msalInstance.setActiveAccount(loginResponse.account);
  }

  return loginResponse.account;
}

// Called from Registration form – reuse logged-in account to get token
export async function getTokenForApi() {
  await ensureInitialized();

  // Try active account first
  let account = msalInstance.getActiveAccount();

  // Fallback to first cached account
  if (!account) {
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
      account = accounts[0];
      msalInstance.setActiveAccount(account);
    }
  }

  if (!account) {
    // No one is logged in
    throw new Error("No signed-in user");
  }

  try {
    const tokenResponse = await msalInstance.acquireTokenSilent({
      ...loginRequest,
      account,
    });

    const token = tokenResponse.accessToken;

    // 🔍 Log decoded JWT claims in browser dev tools (for tracing/debugging)
    const decoded = decodeJwt(token);
    if (decoded && typeof window !== "undefined") {
      console.log("🔑 JWT for API (decoded claims):", decoded);
    }

    return token;
  } catch (err) {
    // If silent fails because interaction is needed, fall back to popup
    if (err instanceof InteractionRequiredAuthError) {
      const tokenResponse = await msalInstance.acquireTokenPopup({
        ...loginRequest,
        account,
      });

      const token = tokenResponse.accessToken;

      const decoded = decodeJwt(token);
      if (decoded && typeof window !== "undefined") {
        console.log("🔑 JWT for API (decoded claims, popup):", decoded);
      }

      return token;
    }
    throw err;
  }
}
