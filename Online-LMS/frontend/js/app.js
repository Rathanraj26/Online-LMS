/* ============================================================
   app.js — Shared utilities used across every page:
   session helpers, toast notifications, navbar rendering,
   and route guarding by role.
   ============================================================ */

/** Returns the logged-in user object from localStorage, or null. */
function getCurrentUser() {
  const raw = localStorage.getItem("rr_user");
  return raw ? JSON.parse(raw) : null;
}

function isLoggedIn() {
  return !!localStorage.getItem("rr_token");
}

function saveSession(token, user) {
  localStorage.setItem("rr_token", token);
  localStorage.setItem("rr_user", JSON.stringify(user));
}

function logoutUser() {
  api.auth.logout().catch(() => {});
  clearSession();
  window.location.href = "login.html";
}

/**
 * Guard a page so only certain roles may view it.
 * Call at the top of a protected page's script.
 * @param {string[]} allowedRoles - e.g. ['student'], ['instructor','admin']
 */
function requireAuth(allowedRoles = []) {
  if (!isLoggedIn()) {
    window.location.href = "login.html";
    return null;
  }
  const user = getCurrentUser();
  if (allowedRoles.length && !allowedRoles.includes(user.role)) {
    window.location.href = "dashboard.html";
    return null;
  }
  return user;
}

/** Lightweight toast notification (success | error). */
function showToast(message, type = "success") {
  document.querySelectorAll(".toast-rr").forEach((el) => el.remove());

  const toast = document.createElement("div");
  toast.className = `toast-rr toast-${type}`;
  const icon = type === "success" ? "bi-check-circle-fill" : "bi-exclamation-circle-fill";
  toast.innerHTML = `<i class="bi ${icon}"></i><span>${escapeHtml(message)}</span>`;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 3500);
}

/** Prevent raw HTML injection when interpolating user-provided text. */
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}

/** Initials for avatar circles, e.g. "Jordan Lee" -> "JL" */
function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
}

function formatDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

/**
 * Renders the left sidebar for dashboard-style pages based on the
 * logged-in user's role. Expects a container with id="sidebarMount".
 */
function renderSidebar(activePage) {
  const mount = document.getElementById("sidebarMount");
  if (!mount) return;
  const user = getCurrentUser();
  if (!user) return;

  const linksByRole = {
    student: [
      { href: "dashboard.html", icon: "bi-grid-1x2-fill", label: "Dashboard" },
      { href: "courses.html", icon: "bi-collection-play-fill", label: "Browse Courses" },
      { href: "assignments.html", icon: "bi-journal-check", label: "Assignments" },
      { href: "quiz.html", icon: "bi-patch-question-fill", label: "Quizzes" },
      { href: "results.html", icon: "bi-bar-chart-fill", label: "Results" },
      { href: "certificate.html", icon: "bi-award-fill", label: "Certificates" },
    ],
    instructor: [
      { href: "dashboard.html", icon: "bi-grid-1x2-fill", label: "Dashboard" },
      { href: "courses.html", icon: "bi-collection-play-fill", label: "My Courses" },
      { href: "assignments.html", icon: "bi-journal-check", label: "Assignments" },
      { href: "quiz.html", icon: "bi-patch-question-fill", label: "Quizzes" },
    ],
    admin: [
      { href: "dashboard.html", icon: "bi-grid-1x2-fill", label: "Overview" },
      { href: "courses.html", icon: "bi-collection-play-fill", label: "All Courses" },
    ],
  };

  const links = linksByRole[user.role] || linksByRole.student;
  const linkHtml = links
    .map(
      (l) => `<a href="${l.href}" class="${activePage === l.href ? "active" : ""}">
        <i class="bi ${l.icon}"></i><span>${l.label}</span>
      </a>`
    )
    .join("");

  mount.innerHTML = `
    <div class="sidebar-brand">
      <span class="brand-badge">RR</span> RR LMS
    </div>
    <nav class="sidebar-nav">
      <div class="nav-group-label">Menu</div>
      ${linkHtml}
      <div class="nav-group-label">Account</div>
      <a href="profile.html" class="${activePage === "profile.html" ? "active" : ""}">
        <i class="bi bi-person-fill"></i><span>Profile</span>
      </a>
      <a href="#" onclick="logoutUser(); return false;">
        <i class="bi bi-box-arrow-right"></i><span>Logout</span>
      </a>
    </nav>
    <div class="sidebar-footer">
      <div class="avatar-sm">${initials(user.name)}</div>
      <div>
        <div class="user-name">${escapeHtml(user.name)}</div>
        <div class="user-role">${escapeHtml(user.role)}</div>
      </div>
    </div>
  `;
}

/** Converts a YouTube watch/share URL into an embeddable iframe src. */
function youtubeEmbedUrl(url) {
  if (!url) return null;
  let videoId = null;
  const watchMatch = url.match(/[?&]v=([^&]+)/);
  const shortMatch = url.match(/youtu\.be\/([^?&]+)/);
  const embedMatch = url.match(/youtube\.com\/embed\/([^?&]+)/);
  if (watchMatch) videoId = watchMatch[1];
  else if (shortMatch) videoId = shortMatch[1];
  else if (embedMatch) videoId = embedMatch[1];
  return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
}

function toggleSidebar() {
  document.querySelector(".sidebar-rr")?.classList.toggle("open");
}

document.addEventListener("DOMContentLoaded", () => {
  // Populate any element flagged with data-user-name / data-user-role
  const user = getCurrentUser();
  if (user) {
    document.querySelectorAll("[data-user-name]").forEach((el) => (el.textContent = user.name));
    document.querySelectorAll("[data-user-role]").forEach((el) => (el.textContent = user.role));
  }
});
