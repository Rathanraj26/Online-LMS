-- ============================================================
-- RR - Online Learning Management System
-- MySQL Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS rr_lms
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE rr_lms;

-- ------------------------------------------------------------
-- USERS  (student | instructor | admin)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(120)  NOT NULL,
    email         VARCHAR(150)  NOT NULL UNIQUE,
    password      VARCHAR(255)  NOT NULL,          -- bcrypt hash
    role          ENUM('student', 'instructor', 'admin') NOT NULL DEFAULT 'student',
    phone         VARCHAR(20)   DEFAULT NULL,
    bio           TEXT          DEFAULT NULL,
    avatar        VARCHAR(255)  DEFAULT NULL,       -- stored filename
    is_active     TINYINT(1)    NOT NULL DEFAULT 1,
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- COURSES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(200)  NOT NULL,
    description    TEXT,
    category       VARCHAR(100)  DEFAULT NULL,
    thumbnail      VARCHAR(255)  DEFAULT NULL,
    price          DECIMAL(10,2) DEFAULT 0.00,
    instructor_id  INT NOT NULL,
    status         ENUM('draft', 'published', 'archived') NOT NULL DEFAULT 'draft',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (instructor_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- COURSE LESSONS / MATERIALS (video, pdf notes etc.)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lessons (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    course_id    INT NOT NULL,
    title        VARCHAR(200) NOT NULL,
    type         ENUM('video', 'youtube', 'pdf', 'link') NOT NULL DEFAULT 'video',
    file_path    VARCHAR(255) DEFAULT NULL,
    duration_min INT DEFAULT 0,
    position     INT DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Migration note: if you already ran this schema before the
-- 'youtube' lesson type was added, upgrade your existing database with:
--   ALTER TABLE lessons MODIFY type ENUM('video','youtube','pdf','link') NOT NULL DEFAULT 'video';
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ENROLLMENTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enrollments (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    course_id    INT NOT NULL,
    enrolled_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_enrollment (user_id, course_id),
    FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- ASSIGNMENTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assignments (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    course_id    INT NOT NULL,
    title        VARCHAR(200) NOT NULL,
    description  TEXT,
    deadline     DATETIME NOT NULL,
    max_marks    INT DEFAULT 100,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- SUBMISSIONS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS submissions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id  INT NOT NULL,
    student_id     INT NOT NULL,
    file           VARCHAR(255) NOT NULL,
    marks_obtained INT DEFAULT NULL,
    feedback       TEXT DEFAULT NULL,
    status         ENUM('submitted', 'graded') NOT NULL DEFAULT 'submitted',
    submitted_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    graded_at      TIMESTAMP NULL DEFAULT NULL,
    UNIQUE KEY uniq_submission (assignment_id, student_id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)    REFERENCES users(id)       ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- QUIZZES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quizzes (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    course_id    INT NOT NULL,
    title        VARCHAR(200) NOT NULL,
    duration_min INT DEFAULT 10,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- QUESTIONS  (options stored as JSON array e.g. ["A","B","C","D"])
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS questions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    quiz_id      INT NOT NULL,
    question     TEXT NOT NULL,
    options      JSON NOT NULL,
    answer       VARCHAR(255) NOT NULL,   -- correct option text/key
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- RESULTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS results (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    student_id   INT NOT NULL,
    quiz_id      INT NOT NULL,
    score        INT NOT NULL DEFAULT 0,
    total        INT NOT NULL DEFAULT 0,
    taken_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (quiz_id)    REFERENCES quizzes(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- PROGRESS  (per-student, per-lesson completion tracking)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS progress (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    student_id     INT NOT NULL,
    course_id      INT NOT NULL,
    lesson_id      INT NOT NULL,
    is_completed   TINYINT(1) DEFAULT 0,
    completed_at   TIMESTAMP NULL DEFAULT NULL,
    UNIQUE KEY uniq_progress (student_id, lesson_id),
    FOREIGN KEY (student_id) REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id)  REFERENCES lessons(id)  ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- CERTIFICATES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS certificates (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    student_id     INT NOT NULL,
    course_id      INT NOT NULL,
    certificate_no VARCHAR(50) NOT NULL UNIQUE,
    date           DATE NOT NULL,
    UNIQUE KEY uniq_certificate (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Seed: default admin account (password = Admin@123 -> bcrypt hash below)
-- Generate your own hash with backend/utils/helper.py::hash_password
-- ------------------------------------------------------------
-- INSERT INTO users (name, email, password, role)
-- VALUES ('System Admin', 'admin@rrlms.com', '<bcrypt-hash-here>', 'admin');
