/* ============================================================
   assignments.js — Assignment listing, submission, and grading.
   ============================================================ */

let selectedCourseId = null;

async function initAssignmentsPage() {
  const user = requireAuth(["student", "instructor", "admin"]);
  if (!user) return;

  await populateCourseSelector(user);

  const selector = document.getElementById("courseSelector");
  selector?.addEventListener("change", () => loadAssignments(selector.value));

  const createForm = document.getElementById("createAssignmentForm");
  if (createForm) createForm.addEventListener("submit", handleCreateAssignment);
}

async function populateCourseSelector(user) {
  const selector = document.getElementById("courseSelector");
  if (!selector) return;

  try {
    const res = user.role === "student" ? await api.enrollment.myCourses() : await api.courses.myCourses();
    const courses = res.data;
    selector.innerHTML =
      `<option value="">Select a course...</option>` +
      courses.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("");

    if (courses.length) {
      selector.value = courses[0].id;
      loadAssignments(courses[0].id);
    }
  } catch (err) {
    showToast(err.message || "Could not load your courses", "error");
  }
}

async function loadAssignments(courseId) {
  selectedCourseId = courseId;
  const list = document.getElementById("assignmentsList");
  if (!list || !courseId) return;

  list.innerHTML = `<div class="empty-state">Loading assignments...</div>`;
  const user = getCurrentUser();

  try {
    const res = await api.assignments.byCourse(courseId);
    const assignments = res.data;

    if (!assignments.length) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon"><i class="bi bi-journal-x"></i></div><p>No assignments yet for this course.</p></div>`;
      return;
    }

    list.innerHTML = assignments
      .map((a) => {
        const overdue = new Date(a.deadline) < new Date();
        return `
        <div class="card-rr p-3 mb-3">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <h3 class="h6 mb-1">${escapeHtml(a.title)}</h3>
              <p class="text-muted-rr mb-2" style="font-size:0.88rem;">${escapeHtml(a.description || "")}</p>
              <span class="pill-rr ${overdue ? "pill-danger" : "pill-brand"}">
                Due ${formatDate(a.deadline)}
              </span>
              <span class="pill-rr pill-warning ms-1">${a.max_marks} marks</span>
            </div>
            <div class="d-flex gap-2">
              ${
                user.role === "student"
                  ? `<button class="btn-rr btn-primary-rr btn-sm-rr" onclick="openSubmitModal(${a.id})"><i class="bi bi-upload"></i> Submit</button>`
                  : `<button class="btn-rr btn-outline-rr btn-sm-rr" onclick="viewSubmissions(${a.id}, '${escapeHtml(a.title)}')"><i class="bi bi-list-check"></i> Submissions</button>
                     <button class="btn-rr btn-danger-rr btn-sm-rr" onclick="deleteAssignment(${a.id})"><i class="bi bi-trash"></i></button>`
              }
            </div>
          </div>
        </div>`;
      })
      .join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
  }
}

async function handleCreateAssignment(event) {
  event.preventDefault();
  const form = event.target;
  const data = {
    course_id: selectedCourseId,
    title: form.title.value.trim(),
    description: form.description.value.trim(),
    deadline: form.deadline.value,
    max_marks: form.max_marks.value || 100,
  };

  if (!selectedCourseId) {
    showToast("Select a course first", "error");
    return;
  }

  try {
    await api.assignments.create(data);
    showToast("Assignment created", "success");
    form.reset();
    bootstrap.Modal.getInstance(document.getElementById("createAssignmentModal"))?.hide();
    loadAssignments(selectedCourseId);
  } catch (err) {
    showToast(err.message || "Could not create assignment", "error");
  }
}

async function deleteAssignment(id) {
  if (!confirm("Delete this assignment? This cannot be undone.")) return;
  try {
    await api.assignments.remove(id);
    showToast("Assignment deleted", "success");
    loadAssignments(selectedCourseId);
  } catch (err) {
    showToast(err.message || "Could not delete assignment", "error");
  }
}

/* ---------------- Student submission ---------------- */
let submittingAssignmentId = null;

function openSubmitModal(assignmentId) {
  submittingAssignmentId = assignmentId;
  const modalEl = document.getElementById("submitAssignmentModal");
  new bootstrap.Modal(modalEl).show();
}

async function handleSubmitAssignment(event) {
  event.preventDefault();
  const form = event.target;
  const file = form.file.files[0];
  if (!file) {
    showToast("Choose a file to submit", "error");
    return;
  }

  const formData = new FormData();
  formData.append("assignment_id", submittingAssignmentId);
  formData.append("file", file);

  try {
    await api.assignments.submit(formData);
    showToast("Assignment submitted!", "success");
    form.reset();
    bootstrap.Modal.getInstance(document.getElementById("submitAssignmentModal"))?.hide();
  } catch (err) {
    showToast(err.message || "Submission failed", "error");
  }
}

/* ---------------- Instructor grading ---------------- */
async function viewSubmissions(assignmentId, title) {
  document.getElementById("submissionsModalTitle").textContent = `Submissions — ${title}`;
  const body = document.getElementById("submissionsModalBody");
  body.innerHTML = "Loading...";
  new bootstrap.Modal(document.getElementById("submissionsModal")).show();

  try {
    const res = await api.assignments.submissions(assignmentId);
    const subs = res.data;
    if (!subs.length) {
      body.innerHTML = `<p class="text-muted-rr">No submissions yet.</p>`;
      return;
    }
    body.innerHTML = subs
      .map(
        (s) => `
      <div class="d-flex justify-content-between align-items-center border-bottom py-2">
        <div>
          <strong>${escapeHtml(s.student_name)}</strong>
          <div class="text-muted-rr" style="font-size:0.8rem;">${escapeHtml(s.student_email)} · Submitted ${formatDate(s.submitted_at)}</div>
        </div>
        <div class="d-flex align-items-center gap-2">
          <a class="btn-rr btn-outline-rr btn-sm-rr" href="${uploadUrl("assignments", s.file)}" target="_blank">View File</a>
          <input type="number" min="0" placeholder="Marks" id="marks-${s.id}" value="${s.marks_obtained ?? ""}" style="width:80px;" class="form-control-rr btn-sm-rr">
          <button class="btn-rr btn-primary-rr btn-sm-rr" onclick="gradeSubmission(${s.id})">Save</button>
        </div>
      </div>`
      )
      .join("");
  } catch (err) {
    body.innerHTML = `<p class="text-muted-rr">${escapeHtml(err.message)}</p>`;
  }
}

async function gradeSubmission(submissionId) {
  const marksInput = document.getElementById(`marks-${submissionId}`);
  const marks = parseInt(marksInput.value, 10);
  if (isNaN(marks)) {
    showToast("Enter valid marks", "error");
    return;
  }
  try {
    await api.assignments.grade(submissionId, { marks_obtained: marks, feedback: "" });
    showToast("Grade saved", "success");
  } catch (err) {
    showToast(err.message || "Could not save grade", "error");
  }
}
