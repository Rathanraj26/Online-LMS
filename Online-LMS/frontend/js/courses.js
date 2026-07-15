/* ============================================================
   courses.js — Course catalog, course details, enrollment,
   instructor course-creation, and the lesson player.
   ============================================================ */

/* ---------------- Catalog (courses.html) ---------------- */
async function loadCourseCatalog() {
  const grid = document.getElementById("catalogGrid");
  if (!grid) return;

  const user = getCurrentUser();
  grid.innerHTML = `<div class="empty-state">Loading courses...</div>`;

  try {
    let courses;
    if (user?.role === "instructor") {
      const res = await api.courses.myCourses();
      courses = res.data;
    } else {
      const search = document.getElementById("searchInput")?.value || "";
      const params = search ? `?search=${encodeURIComponent(search)}` : "";
      const res = await api.courses.all(params);
      courses = res.data;
    }
    renderCourseGrid(courses, grid, user);
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Could not load courses: ${escapeHtml(err.message)}</div>`;
  }
}

function renderCourseGrid(courses, grid, user) {
  if (!courses || courses.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <div class="empty-icon"><i class="bi bi-inboxes"></i></div>
        <p>No courses found yet.</p>
      </div>`;
    return;
  }

  grid.innerHTML = courses
    .map(
      (c) => `
      <a href="course-details.html?id=${c.id}" class="course-card">
        <div class="course-thumb">
          ${c.thumbnail ? `<img src="${uploadUrl("courses", c.thumbnail)}" alt="" style="width:100%;height:100%;object-fit:cover;">` : `<i class="bi bi-mortarboard"></i>`}
        </div>
        <div class="course-body">
          <span class="course-category">${escapeHtml(c.category || "General")}</span>
          <h3 class="course-title">${escapeHtml(c.title)}</h3>
          <div class="course-meta">
            <span><i class="bi bi-person"></i> ${escapeHtml(c.instructor_name || "")}</span>
            <span><i class="bi bi-people"></i> ${c.enrolled_count ?? 0}</span>
          </div>
        </div>
      </a>`
    )
    .join("");
}

function searchCourses() {
  loadCourseCatalog();
}

/* ---------------- Course details (course-details.html) ---------------- */
let currentCourseDetail = null;

async function loadCourseDetails() {
  const container = document.getElementById("courseDetailContainer");
  if (!container) return;

  const courseId = new URLSearchParams(location.search).get("id");
  const user = getCurrentUser();

  try {
    const res = await api.courses.detail(courseId);
    const course = res.data;
    currentCourseDetail = course;

    let isEnrolled = false;
    if (user?.role === "student") {
      try {
        const enrolledRes = await api.enrollment.myCourses();
        isEnrolled = enrolledRes.data.some((c) => c.id == courseId);
      } catch (_) {}
    }

    document.getElementById("courseHeroTitle").textContent = course.title;
    document.getElementById("courseHeroDesc").textContent = course.description;
    document.getElementById("courseHeroCategory").textContent = course.category || "General";
    document.getElementById("instructorName").textContent = course.instructor_name;
    document.getElementById("instructorInitials").textContent = initials(course.instructor_name);

    const actionArea = document.getElementById("courseActionArea");
    if (user?.role === "student") {
      actionArea.innerHTML = isEnrolled
        ? `<a href="learning.html?id=${course.id}" class="btn-rr btn-accent-rr"><i class="bi bi-play-fill"></i> Continue Learning</a>`
        : `<button class="btn-rr btn-accent-rr" onclick="enrollInCourse(${course.id})"><i class="bi bi-plus-lg"></i> Enroll Now</button>`;
    } else {
      const isOwner = user?.role === "admin" || (user?.role === "instructor" && course.instructor_id === user.id);
      actionArea.innerHTML = isOwner
        ? `<button class="btn-rr btn-danger-rr" onclick="deleteCourse(${course.id})"><i class="bi bi-trash"></i> Delete Course</button>`
        : "";
    }

    renderCurriculumList(course.lessons);
  } catch (err) {
    container.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
  }
}

/** Instructor (owner) / admin: permanently delete this course and everything under it. */
async function deleteCourse(courseId) {
  const confirmed = confirm(
    "Delete this ENTIRE course? All modules, enrollments, assignments, quizzes, and results tied to it will be permanently removed. This cannot be undone."
  );
  if (!confirmed) return;

  try {
    await api.courses.remove(courseId);
    showToast("Course deleted", "success");
    setTimeout(() => (window.location.href = "courses.html"), 700);
  } catch (err) {
    showToast(err.message || "Could not delete course", "error");
  }
}

function renderCurriculumList(lessons) {
  const list = document.getElementById("curriculumList");
  if (!list) return;

  const user = getCurrentUser();
  const isOwner =
    currentCourseDetail &&
    (user?.role === "admin" || (user?.role === "instructor" && currentCourseDetail.instructor_id === user.id));

  if (!lessons || lessons.length === 0) {
    list.innerHTML = `<p class="text-muted-rr">No lessons published yet.</p>`;
    return;
  }

  const iconFor = (type) =>
    type === "video" ? "bi-play-fill" : type === "youtube" ? "bi-youtube" : type === "pdf" ? "bi-file-earmark-pdf" : "bi-link-45deg";

  // Lessons already arrive ordered by `position` from the backend (ORDER BY position ASC).
  // We number them sequentially here so the curriculum always reads Module 01, 02, 03...
  // regardless of what position values were actually stored.
  list.innerHTML = lessons
    .map((l, idx) => {
      const moduleLabel = `Module ${String(idx + 1).padStart(2, "0")}`;
      return `
    <div class="lesson-row">
      <div class="lesson-icon"><i class="bi ${iconFor(l.type)}"></i></div>
      <div>
        <div class="lesson-module-label">${moduleLabel}</div>
        <div class="lesson-title">${escapeHtml(l.title)}</div>
      </div>
      <div class="lesson-duration">${l.duration_min ? l.duration_min + " min" : ""}</div>
      ${
        isOwner
          ? `<button type="button" class="btn-rr btn-outline-rr btn-sm-rr ms-2" onclick="deleteLesson(${l.id})" title="Delete module">
               <i class="bi bi-trash"></i>
             </button>`
          : ""
      }
    </div>`;
    })
    .join("");
}

/** Instructor: remove a module/lesson from the curriculum. */
async function deleteLesson(lessonId) {
  if (!confirm("Delete this module? This cannot be undone.")) return;
  const courseId = new URLSearchParams(location.search).get("id");

  try {
    await api.courses.deleteLesson(courseId, lessonId);
    showToast("Module deleted", "success");
    const lessonsRes = await api.courses.lessons(courseId);
    renderCurriculumList(lessonsRes.data);
  } catch (err) {
    showToast(err.message || "Could not delete module", "error");
  }
}

/** Instructor: add a lesson/module to the currently-viewed course. */
async function handleAddLesson(event) {
  event.preventDefault();
  const form = event.target;
  const courseId = new URLSearchParams(location.search).get("id");
  const submitBtn = form.querySelector('button[type="submit"]');

  const formData = new FormData(form);

  submitBtn.disabled = true;
  submitBtn.textContent = "Adding...";

  try {
    await api.courses.addLesson(courseId, formData);
    showToast("Module added to curriculum", "success");
    form.reset();
    if (typeof toggleLessonFileHint === "function") toggleLessonFileHint();
    bootstrap.Modal.getInstance(document.getElementById("addLessonModal"))?.hide();

    // Refresh just the lesson list without a full page reload
    const lessonsRes = await api.courses.lessons(courseId);
    renderCurriculumList(lessonsRes.data);
  } catch (err) {
    showToast(err.message || "Could not add lesson", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Add to Curriculum";
  }
}

async function enrollInCourse(courseId) {
  try {
    await api.enrollment.enroll(courseId);
    showToast("Enrolled successfully!", "success");
    setTimeout(() => (window.location.href = `learning.html?id=${courseId}`), 700);
  } catch (err) {
    showToast(err.message || "Could not enroll", "error");
  }
}

/* ---------------- Instructor: create course (courses.html modal) ---------------- */
async function handleCreateCourse(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  const submitBtn = form.querySelector('button[type="submit"]');

  submitBtn.disabled = true;
  submitBtn.textContent = "Creating...";

  try {
    await api.courses.create(formData, true);
    showToast("Course created successfully", "success");
    form.reset();
    bootstrap.Modal.getInstance(document.getElementById("createCourseModal"))?.hide();
    loadCourseCatalog();
  } catch (err) {
    showToast(err.message || "Could not create course", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Create Course";
  }
}

/* ---------------- Learning player (learning.html) ---------------- */
let currentLessons = [];
let currentLessonIndex = 0;
let currentCourseId = null;

async function loadLearningPlayer() {
  const playlistEl = document.getElementById("lessonPlaylist");
  if (!playlistEl) return;

  currentCourseId = new URLSearchParams(location.search).get("id");

  try {
    const [courseRes, lessonsRes] = await Promise.all([
      api.courses.detail(currentCourseId),
      api.courses.lessons(currentCourseId),
    ]);
    document.getElementById("learningCourseTitle").textContent = courseRes.data.title;
    currentLessons = lessonsRes.data;

    playlistEl.innerHTML = currentLessons
      .map(
        (l, idx) => `
      <div class="playlist-item" id="playlist-item-${idx}" onclick="playLesson(${idx})">
        <i class="bi ${l.type === "video" ? "bi-play-circle" : l.type === "youtube" ? "bi-youtube" : l.type === "link" ? "bi-link-45deg" : "bi-file-earmark-pdf"}"></i>
        <span><strong>Module ${String(idx + 1).padStart(2, "0")}</strong> — ${escapeHtml(l.title)}</span>
      </div>`
      )
      .join("");

    if (currentLessons.length) playLesson(0);
    refreshProgressBar();
  } catch (err) {
    showToast(err.message || "Could not load course content", "error");
  }
}

function playLesson(index) {
  currentLessonIndex = index;
  const lesson = currentLessons[index];
  document.querySelectorAll(".playlist-item").forEach((el) => el.classList.remove("active"));
  document.getElementById(`playlist-item-${index}`)?.classList.add("active");

  const frame = document.getElementById("videoFrame");
  document.getElementById("nowPlayingTitle").textContent = lesson.title;

  if (lesson.type === "video" && lesson.file_path) {
    frame.innerHTML = `<video controls style="width:100%;height:100%;border-radius:16px;" src="${uploadUrl("courses", lesson.file_path)}"></video>`;
  } else if (lesson.type === "youtube" && lesson.file_path) {
    const embedUrl = youtubeEmbedUrl(lesson.file_path);
    frame.innerHTML = embedUrl
      ? `<iframe style="width:100%;height:100%;border-radius:16px;border:none;" src="${embedUrl}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`
      : `<a class="btn-rr btn-outline-rr" style="color:#fff;border-color:rgba(255,255,255,0.3);" href="${escapeHtml(lesson.file_path)}" target="_blank"><i class="bi bi-youtube"></i> Watch on YouTube</a>`;
  } else if (lesson.type === "link" && lesson.file_path) {
    frame.innerHTML = `<a class="btn-rr btn-outline-rr" style="color:#fff;border-color:rgba(255,255,255,0.3);" href="${escapeHtml(lesson.file_path)}" target="_blank"><i class="bi bi-box-arrow-up-right"></i> Open Resource</a>`;
  } else if (lesson.file_path) {
    frame.innerHTML = `<a class="btn-rr btn-outline-rr" style="color:#fff;border-color:rgba(255,255,255,0.3);" href="${uploadUrl("courses", lesson.file_path)}" target="_blank"><i class="bi bi-download"></i> Download Notes (PDF)</a>`;
  } else {
    frame.innerHTML = `<i class="bi bi-film"></i>`;
  }
}

async function markCurrentLessonComplete() {
  const lesson = currentLessons[currentLessonIndex];
  if (!lesson) return;
  try {
    await api.progress.markComplete(currentCourseId, lesson.id);
    document.getElementById(`playlist-item-${currentLessonIndex}`)?.classList.add("active");
    showToast("Lesson marked as complete", "success");
    refreshProgressBar();
  } catch (err) {
    showToast(err.message || "Could not update progress", "error");
  }
}

async function refreshProgressBar() {
  const bar = document.getElementById("courseProgressFill");
  const label = document.getElementById("courseProgressLabel");
  if (!bar) return;
  try {
    const res = await api.progress.get(currentCourseId);
    bar.style.width = `${res.data.percentage}%`;
    label.textContent = `${res.data.percentage}% complete`;
  } catch (_) {}
}
