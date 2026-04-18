redirectIfAuthenticated();

const apiBaseUrlInput = document.querySelector("#api-base-url");
const backendUrlLabel = document.querySelector("#backend-url-label");
const sessionState = document.querySelector("#session-state");
const flashMessage = document.querySelector("#flash-message");
const output = document.querySelector("#response-output");

function syncLoginPage() {
  const apiBaseUrl = getApiBaseUrl();
  apiBaseUrlInput.value = apiBaseUrl;
  backendUrlLabel.textContent = apiBaseUrl;
  sessionState.textContent = getStoredToken() ? "Bearer token stored" : "No token stored";
}

function showFlashMessage(message, type = "success") {
  flashMessage.hidden = false;
  flashMessage.textContent = message;
  flashMessage.classList.remove("is-error", "is-success");
  flashMessage.classList.add(type === "error" ? "is-error" : "is-success");
}

document.querySelector("#login-form").addEventListener("submit", async (event) => {
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
  showJson(output, `POST /auth/login -> ${response.status}`, data);

  if (response.ok && data.access_token) {
    setStoredToken(data.access_token);
    showFlashMessage("Login successful. Redirecting to workspace.");
    window.location.href = "./main.html";
  } else {
    showFlashMessage(data.detail || "Login failed.", "error");
  }
});

apiBaseUrlInput.addEventListener("input", () => {
  setApiBaseUrl(apiBaseUrlInput.value);
  syncLoginPage();
});

syncLoginPage();
const urlParams = new URLSearchParams(window.location.search);
const username = urlParams.get("username");
if (username) {
  document.querySelector("#login-username").value = username;
}
