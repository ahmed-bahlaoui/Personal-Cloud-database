redirectIfLoggedOut();

const apiBaseUrlInput = document.querySelector("#api-base-url");
const backendUrlLabel = document.querySelector("#backend-url-label");
const sessionState = document.querySelector("#session-state");
const flashMessage = document.querySelector("#flash-message");
const output = document.querySelector("#response-output");
const folderSelect = document.querySelector("#folder-select");
const parentFolderSelect = document.querySelector("#parent-folder-select");
const folderList = document.querySelector("#folder-list");
const fileList = document.querySelector("#file-list");
const folderCount = document.querySelector("#folder-count");
const fileCount = document.querySelector("#file-count");

function syncMainPage() {
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

function renderFolders(folders) {
  folderCount.textContent = String(folders.length);
  folderSelect.innerHTML = '<option value="">Root</option>';
  parentFolderSelect.innerHTML = '<option value="">Root</option>';
  if (!folders.length) {
    folderList.innerHTML = '<li class="empty-state">No folders available.</li>';
    return;
  }

  folderList.innerHTML = folders.map((folder) => {
    [folderSelect, parentFolderSelect].forEach((select) => {
      const option = document.createElement("option");
      option.value = String(folder.id);
      option.textContent = `${folder.name} (#${folder.id})`;
      select.appendChild(option);
    });

    return `
      <li>
        <span class="collection-name">${folder.name}</span>
        <span class="collection-meta">id: ${folder.id} · parent: ${folder.parent_folder_id ?? "root"}</span>
      </li>
    `;
  }).join("");
}

function renderFiles(files) {
  fileCount.textContent = String(files.length);
  if (!files.length) {
    fileList.innerHTML = '<li class="empty-state">No files uploaded yet.</li>';
    return;
  }

  fileList.innerHTML = files.map((file) => `
    <li>
      <span class="collection-name">${file.original_name}</span>
      <span class="collection-meta">folder: ${file.folder_id ?? "root"} · ${file.size_bytes} bytes</span>
    </li>
  `).join("");
}

async function loadWorkspaceData() {
  const headers = getAuthHeaders();

  const [foldersResponse, filesResponse] = await Promise.all([
    fetch(`${getApiBaseUrl()}/folders`, { headers }),
    fetch(`${getApiBaseUrl()}/files`, { headers }),
  ]);

  const foldersData = await parseResponse(foldersResponse);
  const filesData = await parseResponse(filesResponse);

  if (foldersResponse.status === 401 || filesResponse.status === 401) {
    clearStoredToken();
    window.location.href = "./login.html";
    return;
  }

  if (foldersResponse.ok) {
    renderFolders(foldersData);
  }
  if (filesResponse.ok) {
    renderFiles(filesData);
  }

  showJson(output, "Workspace data refreshed", {
    foldersStatus: foldersResponse.status,
    filesStatus: filesResponse.status,
    folders: foldersData,
    files: filesData,
  });
}

document.querySelector("#fetch-me").addEventListener("click", async () => {
  const response = await fetch(`${getApiBaseUrl()}/auth/me`, {
    headers: getAuthHeaders(),
  });
  const data = await parseResponse(response);
  showJson(output, `GET /auth/me -> ${response.status}`, data);

  if (response.status === 401) {
    clearStoredToken();
    window.location.href = "./login.html";
    return;
  }

  if (response.ok) {
    showFlashMessage(`Authenticated as ${data.username}.`);
  } else {
    showFlashMessage(data.detail || "Could not fetch current user.", "error");
  }
});

document.querySelector("#logout-button").addEventListener("click", () => {
  clearStoredToken();
  window.location.href = "./login.html";
});

document.querySelector("#refresh-data").addEventListener("click", loadWorkspaceData);

document.querySelector("#create-folder-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: document.querySelector("#folder-name").value,
    parent_folder_id: parentFolderSelect.value ? Number(parentFolderSelect.value) : null,
  };

  const response = await fetch(`${getApiBaseUrl()}/folders`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await parseResponse(response);
  showJson(output, `POST /folders -> ${response.status}`, data);

  if (response.status === 401) {
    clearStoredToken();
    window.location.href = "./login.html";
    return;
  }

  if (response.ok) {
    showFlashMessage(`Created folder ${data.name}.`);
    document.querySelector("#create-folder-form").reset();
    await loadWorkspaceData();
  } else {
    showFlashMessage(data.detail || "Folder creation failed.", "error");
  }
});

document.querySelector("#upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const fileInput = document.querySelector("#upload-file");
  const selectedFile = fileInput.files[0];

  if (!selectedFile) {
    showFlashMessage("Choose a file before uploading.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);
  if (folderSelect.value) {
    formData.append("folder_id", folderSelect.value);
  }

  const response = await fetch(`${getApiBaseUrl()}/files`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });

  const data = await parseResponse(response);
  showJson(output, `POST /files -> ${response.status}`, data);

  if (response.status === 401) {
    clearStoredToken();
    window.location.href = "./login.html";
    return;
  }

  if (response.ok) {
    showFlashMessage(`Uploaded ${data.original_name} successfully.`);
    document.querySelector("#upload-form").reset();
    await loadWorkspaceData();
  } else {
    showFlashMessage(data.detail || "Upload failed.", "error");
  }
});

apiBaseUrlInput.addEventListener("input", () => {
  setApiBaseUrl(apiBaseUrlInput.value);
  syncMainPage();
});

syncMainPage();
loadWorkspaceData();
