const tabs = [...document.querySelectorAll(".auth-tab")];
const panels = [...document.querySelectorAll(".auth-form")];
const feedbackEl = document.getElementById("auth-feedback");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const fieldErrorIds = [
  "login-email-error",
  "login-password-error",
  "register-name-error",
  "register-email-error",
  "register-password-error",
];

function clearFeedback() {
  feedbackEl.hidden = true;
  feedbackEl.textContent = "";
  feedbackEl.className = "auth-feedback";
  fieldErrorIds.forEach((id) => {
    const node = document.getElementById(id);
    if (node) node.textContent = "";
  });
  document.querySelectorAll(".auth-form input").forEach((input) => input.classList.remove("has-error"));
}

function showFeedback(message, type = "error") {
  feedbackEl.hidden = false;
  feedbackEl.textContent = message;
  feedbackEl.className = `auth-feedback ${type}`;
}

function setFieldError(inputId, errorId, message) {
  const input = document.getElementById(inputId);
  const error = document.getElementById(errorId);
  if (input) input.classList.add("has-error");
  if (error) error.textContent = message;
}

function setTab(view) {
  tabs.forEach((tab) => tab.classList.toggle("is-active", tab.dataset.authView === view));
  panels.forEach((panel) => panel.classList.toggle("is-active", panel.dataset.authPanel === view));
  clearFeedback();
}

async function sendAuth(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Authentication failed.");
  }
  window.location.href = "/terminal";
}

function validateLogin() {
  clearFeedback();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  let valid = true;

  if (!email) {
    setFieldError("login-email", "login-email-error", "Email is required.");
    valid = false;
  }
  if (!password) {
    setFieldError("login-password", "login-password-error", "Password is required.");
    valid = false;
  }
  if (!valid) {
    showFeedback("Enter your login details to continue.");
  }
  return valid;
}

function validateRegister() {
  clearFeedback();
  const name = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;
  let valid = true;

  if (!name) {
    setFieldError("register-name", "register-name-error", "Name is required.");
    valid = false;
  }
  if (!email) {
    setFieldError("register-email", "register-email-error", "Email is required.");
    valid = false;
  }
  if (!password) {
    setFieldError("register-password", "register-password-error", "Password is required.");
    valid = false;
  } else if (password.length < 8) {
    setFieldError("register-password", "register-password-error", "Use at least 8 characters.");
    valid = false;
  }
  if (!valid) {
    showFeedback("Fix the highlighted fields before creating an account.");
  }
  return valid;
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => setTab(tab.dataset.authView));
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!validateLogin()) return;
  try {
    await sendAuth("/auth/login", {
      email: document.getElementById("login-email").value,
      password: document.getElementById("login-password").value,
    });
  } catch (error) {
    showFeedback(error.message);
  }
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!validateRegister()) return;
  try {
    await sendAuth("/auth/register", {
      name: document.getElementById("register-name").value,
      email: document.getElementById("register-email").value,
      password: document.getElementById("register-password").value,
    });
  } catch (error) {
    showFeedback(error.message);
  }
});

fetch("/auth/me").then((response) => {
  if (response.ok) {
    window.location.href = "/terminal";
  }
});
