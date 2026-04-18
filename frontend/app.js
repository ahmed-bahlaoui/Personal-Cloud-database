const apiBaseUrlInput = document.querySelector("#api-base-url");
const backendUrlLabel = document.querySelector("#backend-url-label");
const sessionState = document.querySelector("#session-state");
const output = document.querySelector("#response-output");
const fetchMeButton = document.querySelector("#fetch-me");
const tabButtons = document.querySelectorAll(".tab");
const forms = document.querySelectorAll(".auth-form");

const TOKEN_KEY = "cloud-vault-access-token";

function getApiBaseUrl() {
  return apiBaseUrlInput.value.trim().replace(/\/$/, "");
}

function setOutput(title, data) {
  output.textContent = `${title}\n\n${JSON.stringify(data, null, 2)}`;
}

function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

function setStoredToken(token) {
  window.localStorage.setItem(TOKEN_KEY, token);
  syncSessionUi();
}

function syncSessionUi() {
  const token = getStoredToken();
  backendUrlLabel.textContent = getApiBaseUrl();
  sessionState.textContent = token ? "Bearer token stored" : "No token stored";
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

async function registerUser(event) {
  event.preventDefault();

  const payload = {
    email: document.querySelector("#register-email").value,
    username: document.querySelector("#register-username").value,
    password: document.querySelector("#register-password").value,
  };

  const response = await fetch(`${getApiBaseUrl()}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await parseResponse(response);
  setOutput(`POST /auth/register -> ${response.status}`, data);
}

async function loginUser(event) {
  event.preventDefault();

  const body = new URLSearchParams({
    username: document.querySelector("#login-username").value,
    password: document.querySelector("#login-password").value,
  });

  const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  const data = await parseResponse(response);
  if (response.ok && data.access_token) {
    setStoredToken(data.access_token);
  }
  setOutput(`POST /auth/login -> ${response.status}`, data);
}

async function fetchCurrentUser() {
  const token = getStoredToken();
  if (!token) {
    setOutput("GET /auth/me -> skipped", {
      detail: "No token stored yet. Log in first.",
    });
    return;
  }

  const response = await fetch(`${getApiBaseUrl()}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  const data = await parseResponse(response);
  setOutput(`GET /auth/me -> ${response.status}`, data);
}

function activateTab(targetFormId) {
  forms.forEach((form) => {
    form.classList.toggle("is-visible", form.id === targetFormId);
  });

  tabButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.target === targetFormId);
  });
}

tabButtons.forEach((button) => {
  button.addEventListener("click", () => activateTab(button.dataset.target));
});

document.querySelector("#register-form").addEventListener("submit", registerUser);
document.querySelector("#login-form").addEventListener("submit", loginUser);
fetchMeButton.addEventListener("click", fetchCurrentUser);
apiBaseUrlInput.addEventListener("input", syncSessionUi);

syncSessionUi();
