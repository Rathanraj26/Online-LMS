/* ============================================================
   api.js — Central fetch wrapper for the RR-LMS backend.
   Every other JS file talks to the backend exclusively through
   the `api` object defined here.
   ============================================================ */

const API_BASE_URL = "http://localhost:5000/api";
const UPLOADS_BASE_URL = "http://localhost:5000/uploads";

const api = {
  /**
   * Core request helper. Automatically attaches the JWT (if present)
   * and normalizes JSON / multipart bodies.
   */
  async request(endpoint, { method = "GET", body = null, isFormData = false } = {}) {
    const headers = {};
    const token = localStorage.getItem("rr_token");
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (!isFormData) headers["Content-Type"] = "application/json";

    const options = { method, headers };
    if (body) options.body = isFormData ? body : JSON.stringify(body);

    let response;
    try {
      response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    } catch (networkErr) {
      // fetch() only throws here for network-level failures (DNS, connection
      // refused, mixed content, CORS preflight failure) — never for 4xx/5xx,
      // which are handled below via response.ok. The overwhelmingly common
      // cause is: the Flask backend isn't running, or isn't running at the
      // address configured in API_BASE_URL above.
      throw {
        message: `Can't reach the backend at ${API_BASE_URL}. Make sure "python app.py" is running in a terminal and shows "Running on http://0.0.0.0:5000" with no errors.`,
        status: 0,
      };
    }

    let payload = {};
    try {
      payload = await response.json();
    } catch (_) {
      /* non-JSON response body */
    }

    if (!response.ok) {
      // Session expired / invalid token → force re-login
      if (response.status === 401) {
        clearSession();
        if (!location.pathname.endsWith("login.html")) {
          window.location.href = "login.html";
        }
      }
      throw { message: payload.message || "Request failed", status: response.status, errors: payload.errors };
    }

    return payload;
  },

  get(endpoint) {
    return api.request(endpoint);
  },
  post(endpoint, body, isFormData = false) {
    return api.request(endpoint, { method: "POST", body, isFormData });
  },
  put(endpoint, body, isFormData = false) {
    return api.request(endpoint, { method: "PUT", body, isFormData });
  },
  delete(endpoint) {
    return api.request(endpoint, { method: "DELETE" });
  },

  // ---------------- Convenience domain methods ----------------
  auth: {
    register: (data) => api.post("/register", data),
    login: (data) => api.post("/login", data),
    logout: () => api.post("/logout"),
  },
  users: {
    all: (role) => api.get(`/users${role ? `?role=${role}` : ""}`),
    profile: () => api.get("/profile"),
    updateProfile: (data, isFormData = false) => api.put("/profile", data, isFormData),
    setStatus: (id, isActive) => api.put(`/users/${id}/status`, { is_active: isActive }),
    remove: (id) => api.delete(`/users/${id}`),
  },
  courses: {
    all: (params = "") => api.get(`/courses${params}`),
    detail: (id) => api.get(`/courses/${id}`),
    create: (data, isFormData = false) => api.post("/courses", data, isFormData),
    update: (id, data) => api.put(`/courses/${id}`, data),
    remove: (id) => api.delete(`/courses/${id}`),
    myCourses: () => api.get("/instructor/courses"),
    lessons: (id) => api.get(`/courses/${id}/lessons`),
    addLesson: (id, formData) => api.post(`/courses/${id}/lessons`, formData, true),
    deleteLesson: (courseId, lessonId) => api.delete(`/courses/${courseId}/lessons/${lessonId}`),
    students: (id) => api.get(`/courses/${id}/students`),
  },
  enrollment: {
    enroll: (courseId) => api.post("/enroll", { course_id: courseId }),
    myCourses: () => api.get("/my-courses"),
  },
  assignments: {
    byCourse: (courseId) => api.get(`/assignments?course_id=${courseId}`),
    create: (data) => api.post("/assignments", data),
    remove: (id) => api.delete(`/assignments/${id}`),
    submit: (formData) => api.post("/submissions", formData, true),
    submissions: (assignmentId) => api.get(`/assignments/${assignmentId}/submissions`),
    grade: (submissionId, data) => api.put(`/submissions/${submissionId}/grade`, data),
  },
  quiz: {
    byCourse: (courseId) => api.get(`/quizzes?course_id=${courseId}`),
    questions: (quizId) => api.get(`/quizzes/${quizId}/questions`),
    create: (data) => api.post("/quizzes", data),
    addQuestion: (quizId, data) => api.post(`/quizzes/${quizId}/questions`, data),
    submit: (data) => api.post("/results", data),
    results: () => api.get("/results"),
  },
  progress: {
    markComplete: (courseId, lessonId) =>
      api.post("/progress/complete", { course_id: courseId, lesson_id: lessonId }),
    get: (courseId) => api.get(`/progress/${courseId}`),
  },
  certificate: {
    generate: (courseId) => api.post(`/certificate/${courseId}`),
    get: (courseId) => api.get(`/certificate/${courseId}`),
  },
};

/** Build the full URL for an uploaded file (avatar, thumbnail, lesson doc, etc.) */
function uploadUrl(folder, filename) {
  if (!filename) return null;
  return `${UPLOADS_BASE_URL}/${folder}/${filename}`;
}

function clearSession() {
  localStorage.removeItem("rr_token");
  localStorage.removeItem("rr_user");
}
