/* ============================================================
   quiz.js — Quiz selection, timed quiz-taking flow, scoring,
   and instructor quiz creation.
   ============================================================ */

let quizQuestions = [];
let quizAnswers = {};
let currentQuestionIndex = 0;
let quizTimerInterval = null;
let quizSecondsRemaining = 0;
let activeQuizId = null;

/* ---------------- Quiz list (quiz.html) ---------------- */
async function initQuizPage() {
  const user = requireAuth(["student", "instructor", "admin"]);
  if (!user) return;

  const selector = document.getElementById("courseSelector");
  if (!selector) return;

  try {
    const res = user.role === "student" ? await api.enrollment.myCourses() : await api.courses.myCourses();
    const courses = res.data;
    selector.innerHTML =
      `<option value="">Select a course...</option>` +
      courses.map((c) => `<option value="${c.id}">${escapeHtml(c.title)}</option>`).join("");
    selector.addEventListener("change", () => loadQuizList(selector.value));
    if (courses.length) {
      selector.value = courses[0].id;
      loadQuizList(courses[0].id);
    }
  } catch (err) {
    showToast(err.message || "Could not load courses", "error");
  }

  document.getElementById("createQuizForm")?.addEventListener("submit", handleCreateQuiz);
}

let selectedCourseForQuiz = null;

async function loadQuizList(courseId) {
  selectedCourseForQuiz = courseId;
  const list = document.getElementById("quizList");
  if (!list || !courseId) return;
  const user = getCurrentUser();

  list.innerHTML = `<div class="empty-state">Loading quizzes...</div>`;
  try {
    const res = await api.quiz.byCourse(courseId);
    const quizzes = res.data;
    if (!quizzes.length) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon"><i class="bi bi-patch-question"></i></div><p>No quizzes available for this course yet.</p></div>`;
      return;
    }
    list.innerHTML = quizzes
      .map(
        (q) => `
      <div class="card-rr p-3 mb-3 d-flex flex-row justify-content-between align-items-center flex-wrap gap-2">
        <div>
          <h3 class="h6 mb-1">${escapeHtml(q.title)}</h3>
          <span class="pill-rr pill-brand"><i class="bi bi-clock"></i> ${q.duration_min} min</span>
        </div>
        ${
          user.role === "student"
            ? `<button class="btn-rr btn-accent-rr btn-sm-rr" onclick="startQuiz(${q.id}, '${escapeHtml(q.title)}', ${q.duration_min})"><i class="bi bi-play-fill"></i> Start Quiz</button>`
            : `<button class="btn-rr btn-outline-rr btn-sm-rr" onclick="openAddQuestion(${q.id})"><i class="bi bi-plus-lg"></i> Add Question</button>`
        }
      </div>`
      )
      .join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
  }
}

/* ---------------- Instructor: create quiz ---------------- */
async function handleCreateQuiz(event) {
  event.preventDefault();
  const form = event.target;
  if (!selectedCourseForQuiz) {
    showToast("Select a course first", "error");
    return;
  }
  try {
    await api.quiz.create({
      course_id: selectedCourseForQuiz,
      title: form.title.value.trim(),
      duration_min: form.duration_min.value || 10,
    });
    showToast("Quiz created", "success");
    form.reset();
    bootstrap.Modal.getInstance(document.getElementById("createQuizModal"))?.hide();
    loadQuizList(selectedCourseForQuiz);
  } catch (err) {
    showToast(err.message || "Could not create quiz", "error");
  }
}

let addingQuestionToQuizId = null;
function openAddQuestion(quizId) {
  addingQuestionToQuizId = quizId;
  new bootstrap.Modal(document.getElementById("addQuestionModal")).show();
}

async function handleAddQuestion(event) {
  event.preventDefault();
  const form = event.target;
  const options = [form.option1.value, form.option2.value, form.option3.value, form.option4.value].filter(Boolean);

  try {
    await api.quiz.addQuestion(addingQuestionToQuizId, {
      question: form.question.value.trim(),
      options,
      answer: form.correctAnswer.value.trim(),
    });
    showToast("Question added", "success");
    form.reset();
    bootstrap.Modal.getInstance(document.getElementById("addQuestionModal"))?.hide();
  } catch (err) {
    showToast(err.message || "Could not add question", "error");
  }
}

/* ---------------- Student: take quiz ---------------- */
async function startQuiz(quizId, title, durationMin) {
  activeQuizId = quizId;
  quizAnswers = {};
  currentQuestionIndex = 0;

  try {
    const res = await api.quiz.questions(quizId);
    quizQuestions = res.data;
    if (!quizQuestions.length) {
      showToast("This quiz has no questions yet", "error");
      return;
    }

    document.getElementById("quizListView").classList.add("d-none");
    document.getElementById("quizTakingView").classList.remove("d-none");
    document.getElementById("activeQuizTitle").textContent = title;

    quizSecondsRemaining = durationMin * 60;
    startQuizTimer();
    renderQuestion();
  } catch (err) {
    showToast(err.message || "Could not load quiz", "error");
  }
}

function startQuizTimer() {
  clearInterval(quizTimerInterval);
  updateTimerDisplay();
  quizTimerInterval = setInterval(() => {
    quizSecondsRemaining--;
    updateTimerDisplay();
    if (quizSecondsRemaining <= 0) {
      clearInterval(quizTimerInterval);
      submitQuiz();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const el = document.getElementById("quizTimer");
  if (!el) return;
  const m = Math.floor(quizSecondsRemaining / 60).toString().padStart(2, "0");
  const s = (quizSecondsRemaining % 60).toString().padStart(2, "0");
  el.innerHTML = `<i class="bi bi-stopwatch"></i> ${m}:${s}`;
  el.classList.toggle("time-critical", quizSecondsRemaining <= 30);
}

function renderQuestion() {
  const q = quizQuestions[currentQuestionIndex];
  const container = document.getElementById("questionContainer");

  const letters = ["A", "B", "C", "D", "E"];
  container.innerHTML = `
    <div class="card-rr question-card">
      <div class="question-number">Question ${currentQuestionIndex + 1} of ${quizQuestions.length}</div>
      <div class="question-text">${escapeHtml(q.question)}</div>
      <div class="option-list">
        ${q.options
          .map(
            (opt, i) => `
          <div class="option-item ${quizAnswers[q.id] === opt ? "selected" : ""}" onclick="selectAnswer(${q.id}, ${JSON.stringify(opt).replace(/"/g, "&quot;")})">
            <span class="option-letter">${letters[i]}</span>
            <span>${escapeHtml(opt)}</span>
          </div>`
          )
          .join("")}
      </div>
    </div>`;

  // progress dots
  const track = document.getElementById("quizProgressTrack");
  track.innerHTML = quizQuestions
    .map((_, i) => {
      let cls = "dot";
      if (i < currentQuestionIndex) cls += " done";
      if (i === currentQuestionIndex) cls += " current";
      return `<div class="${cls}"></div>`;
    })
    .join("");

  document.getElementById("prevBtn").disabled = currentQuestionIndex === 0;
  document.getElementById("nextBtn").textContent =
    currentQuestionIndex === quizQuestions.length - 1 ? "Submit Quiz" : "Next";
}

function selectAnswer(questionId, answer) {
  quizAnswers[questionId] = answer;
  renderQuestion();
}

function goToPrevQuestion() {
  if (currentQuestionIndex > 0) {
    currentQuestionIndex--;
    renderQuestion();
  }
}

function goToNextQuestion() {
  if (currentQuestionIndex < quizQuestions.length - 1) {
    currentQuestionIndex++;
    renderQuestion();
  } else {
    submitQuiz();
  }
}

async function submitQuiz() {
  clearInterval(quizTimerInterval);
  try {
    const res = await api.quiz.submit({ quiz_id: activeQuizId, answers: quizAnswers });
    showQuizResult(res.data.score, res.data.total);
  } catch (err) {
    showToast(err.message || "Could not submit quiz", "error");
  }
}

function showQuizResult(score, total) {
  document.getElementById("quizTakingView").classList.add("d-none");
  const resultView = document.getElementById("quizResultView");
  resultView.classList.remove("d-none");

  const pct = total ? Math.round((score / total) * 100) : 0;
  resultView.innerHTML = `
    <div class="card-rr result-hero">
      <div class="score-ring" style="--pct:${pct}">
        <span class="score-text">${pct}%</span>
      </div>
      <h2>${score} / ${total} correct</h2>
      <p class="text-muted-rr">Great effort! Your result has been saved.</p>
      <a href="results.html" class="btn-rr btn-primary-rr mt-2">View All Results</a>
      <button class="btn-rr btn-outline-rr mt-2" onclick="location.reload()">Back to Quizzes</button>
    </div>`;
}
