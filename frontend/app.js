const loginButton = document.getElementById("login-btn");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const statusMessage = document.getElementById("status");
const usersList = document.getElementById("users-list");
const createUserButton = document.getElementById("create-user-btn");
const newNameInput = document.getElementById("new-name");
const newRoleInput = document.getElementById("new-role");
const newEmailInput = document.getElementById("new-email");
const simulateApiFailureCheckbox = document.getElementById("simulate-api-failure");

let accessToken = null;

function renderUsers(users) {
  usersList.innerHTML = "";
  users.forEach((user) => {
    const item = document.createElement("li");
    item.setAttribute("data-testid", `user-item-${user.id}`);
    item.textContent = `${user.id} - ${user.name} (${user.role}) - ${user.email}`;

    const editButton = document.createElement("button");
    editButton.textContent = "Edit";
    editButton.setAttribute("data-testid", `edit-user-btn-${user.id}`);
    editButton.className = "small-btn";
    editButton.addEventListener("click", () => editUser(user));

    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.setAttribute("data-testid", `delete-user-btn-${user.id}`);
    deleteButton.className = "small-btn danger-btn";
    deleteButton.addEventListener("click", () => deleteUser(user.id));

    item.appendChild(editButton);
    item.appendChild(deleteButton);
    usersList.appendChild(item);
  });
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${accessToken}`,
  };
}

async function loadUsers() {
  statusMessage.textContent = "Loading...";

  try {
    const usersPath = simulateApiFailureCheckbox.checked ? "/users-broken" : "/users";
    const usersResponse = await fetch(usersPath, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!usersResponse.ok) {
      statusMessage.textContent = "Failed to load users";
      return;
    }

    const users = await usersResponse.json();
    renderUsers(users);
    statusMessage.textContent = `Loaded ${users.length} users`;
  } catch (error) {
    statusMessage.textContent = "API error. Is the backend running?";
  }
}

async function loginAndLoadUsers() {
  statusMessage.textContent = "Loading...";
  usersList.innerHTML = "";

  try {
    const loginResponse = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: usernameInput.value,
        password: passwordInput.value,
      }),
    });

    if (!loginResponse.ok) {
      statusMessage.textContent = "Login failed";
      return;
    }

    const loginData = await loginResponse.json();
    accessToken = loginData.token;
    await loadUsers();
  } catch (error) {
    statusMessage.textContent = "API error. Is the backend running?";
  }
}

async function createUser() {
  if (!accessToken) {
    statusMessage.textContent = "Please login first";
    return;
  }

  if (!newNameInput.value || !newRoleInput.value || !newEmailInput.value) {
    statusMessage.textContent = "Validation: all create-user fields are required";
    return;
  }

  statusMessage.textContent = "Creating user...";

  try {
    const response = await fetch("/users", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        name: newNameInput.value,
        role: newRoleInput.value,
        email: newEmailInput.value,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      statusMessage.textContent = `Create failed: ${errorData.detail || "unknown error"}`;
      return;
    }

    newNameInput.value = "";
    newRoleInput.value = "";
    newEmailInput.value = "";
    await loadUsers();
  } catch (error) {
    statusMessage.textContent = "API error. Is the backend running?";
  }
}

async function editUser(user) {
  if (!accessToken) {
    statusMessage.textContent = "Please login first";
    return;
  }

  const nextName = window.prompt("Update name", user.name);
  if (nextName === null) return;
  const nextRole = window.prompt("Update role", user.role);
  if (nextRole === null) return;
  const nextEmail = window.prompt("Update email", user.email);
  if (nextEmail === null) return;

  statusMessage.textContent = "Updating user...";

  try {
    const response = await fetch(`/users/${user.id}`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({
        name: nextName,
        role: nextRole,
        email: nextEmail,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      statusMessage.textContent = `Update failed: ${errorData.detail || "unknown error"}`;
      return;
    }

    await loadUsers();
  } catch (error) {
    statusMessage.textContent = "API error. Is the backend running?";
  }
}

async function deleteUser(userId) {
  if (!accessToken) {
    statusMessage.textContent = "Please login first";
    return;
  }

  statusMessage.textContent = "Deleting user...";

  try {
    const response = await fetch(`/users/${userId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json();
      statusMessage.textContent = `Delete failed: ${errorData.detail || "unknown error"}`;
      return;
    }

    await loadUsers();
  } catch (error) {
    statusMessage.textContent = "API error. Is the backend running?";
  }
}

loginButton.addEventListener("click", loginAndLoadUsers);
createUserButton.addEventListener("click", createUser);
