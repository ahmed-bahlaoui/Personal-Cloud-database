redirectIfAuthenticated();

const apiBaseUrlInput = document.querySelector("#api-base-url");
const backendUrlLabel = document.querySelector("#backend-url-label");
const sessionState = document.querySelector("#session-state");
const flashMessage = document.querySelector("#flash-message");
const output = document.querySelector("#response-output");

function syncRegisterPage() {
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

document.querySelector("#register-form").addEventListener("submit", async (event) => {
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
  showJson(output, `POST /auth/register -> ${response.status}`, data);

  if (response.ok) {
    showFlashMessage("Account created. Redirecting to login.");
    window.location.href = `./login.html?username=${encodeURIComponent(payload.username)}`;
  } else {
    showFlashMessage(data.detail || "Registration failed.", "error");
  }
});

apiBaseUrlInput.addEventListener("input", () => {
  setApiBaseUrl(apiBaseUrlInput.value);
  syncRegisterPage();
});

syncRegisterPage();
