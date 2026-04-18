const TOKEN_KEY = "cloud-vault-access-token";
const API_BASE_URL_KEY = "cloud-vault-api-base-url";
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

function getApiBaseUrl() {
  return (window.localStorage.getItem(API_BASE_URL_KEY) || DEFAULT_API_BASE_URL)
    .trim()
    .replace(/\/$/, "");
}

function setApiBaseUrl(value) {
  window.localStorage.setItem(API_BASE_URL_KEY, value.trim().replace(/\/$/, ""));
}

function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

function setStoredToken(token) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

function clearStoredToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

function getAuthHeaders() {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function showJson(target, title, data) {
  target.textContent = `${title}\n\n${JSON.stringify(data, null, 2)}`;
}

function redirectIfAuthenticated() {
  if (getStoredToken()) {
    window.location.href = "./main.html";
  }
}

function redirectIfLoggedOut() {
  if (!getStoredToken()) {
    window.location.href = "./login.html";
  }
}
