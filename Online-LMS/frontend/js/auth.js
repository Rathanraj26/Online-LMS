/* ============================================================
   auth.js — Handles the login and register forms.
   ============================================================ */

// Redirect already-logged-in users straight to their dashboard
document.addEventListener("DOMContentLoaded", () => {
  if (isLoggedIn() && (location.pathname.endsWith("login.html") || location.pathname.endsWith("register.html"))) {
    window.location.href = "dashboard.html";
  }
});

/* ---------------- Register role toggle (register.html) ---------------- */
let selectedRole = "student";
function selectRole(role, btnEl) {
  selectedRole = role;
  document.querySelectorAll(".auth-role-toggle button").forEach((b) => b.classList.remove("active"));
  btnEl.classList.add("active");
}

/* ---------------- Login form ---------------- */
async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const email = form.email.value.trim();
  const password = form.password.value;
  const submitBtn = form.querySelector('button[type="submit"]');

  clearFieldErrors(form);
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Signing in...`;

  try {
    const res = await api.auth.login({ email, password });
    saveSession(res.data.token, res.data.user);
    showToast("Welcome back! Redirecting...", "success");
    setTimeout(() => (window.location.href = "dashboard.html"), 600);
  } catch (err) {
    showToast(err.message || "Login failed", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = "Sign In";
  }
}

/* ---------------- Register form ---------------- */
async function handleRegister(event) {
  event.preventDefault();
  const form = event.target;
  const name = form.name.value.trim();
  const email = form.email.value.trim();
  const password = form.password.value;
  const confirmPassword = form.confirmPassword.value;
  const submitBtn = form.querySelector('button[type="submit"]');

  clearFieldErrors(form);

  if (password !== confirmPassword) {
    showFieldError(form.confirmPassword, "Passwords do not match");
    return;
  }
  if (password.length < 6) {
    showFieldError(form.password, "Password must be at least 6 characters");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Creating account...`;

  try {
    const res = await api.auth.register({ name, email, password, role: selectedRole });
    saveSession(res.data.token, res.data.user);
    showToast("Account created! Redirecting...", "success");
    setTimeout(() => (window.location.href = "dashboard.html"), 600);
  } catch (err) {
    if (err.errors) {
      showToast(err.errors.join(", "), "error");
    } else {
      showToast(err.message || "Registration failed", "error");
    }
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = "Create Account";
  }
}

function showFieldError(inputEl, message) {
  const errorEl = inputEl.closest(".form-group")?.querySelector(".field-error");
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.style.display = "block";
  }
  inputEl.style.borderColor = "var(--danger)";
}

function clearFieldErrors(form) {
  form.querySelectorAll(".field-error").forEach((el) => (el.style.display = "none"));
  form.querySelectorAll(".form-control-rr").forEach((el) => (el.style.borderColor = ""));
}
