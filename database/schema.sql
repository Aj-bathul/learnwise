

CREATE DATABASE IF NOT EXISTS learnwise CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE learnwise;


CREATE TABLE roles (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(20) NOT NULL UNIQUE  
);

INSERT INTO roles (name) VALUES ('student'), ('admin');


CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role_id         INT NOT NULL,
    interests       VARCHAR(255) NULL,          
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);


CREATE TABLE courses (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    source_course_id    VARCHAR(100) NULL,      
    title               VARCHAR(255) NOT NULL,
    organization        VARCHAR(150) NULL,
    description         TEXT,
    skills              VARCHAR(500) NULL,
    difficulty_level    ENUM('Beginner','Intermediate','Advanced','Mixed') DEFAULT 'Mixed',
    rating              DECIMAL(3,2) NULL,
    review_count        INT NULL,
    course_url          VARCHAR(500) NULL,
    category            VARCHAR(150) NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE lessons (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    course_id    INT NOT NULL,
    title        VARCHAR(255) NOT NULL,
    video_url    VARCHAR(500),
    content      TEXT,
    order_index  INT DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);


CREATE TABLE enrollments (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT NOT NULL,
    course_id         INT NOT NULL,
    enrolled_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status            ENUM('active','completed','dropped') DEFAULT 'active',
    progress_percent  DECIMAL(5,2) DEFAULT 0.00,
    UNIQUE KEY uniq_enrollment (user_id, course_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);


CREATE TABLE quizzes (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    course_id    INT NOT NULL,
    lesson_id    INT NULL,
    title        VARCHAR(255) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE SET NULL
);


CREATE TABLE questions (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    quiz_id          INT NOT NULL,
    question_text    TEXT NOT NULL,
    option_a         VARCHAR(255) NOT NULL,
    option_b         VARCHAR(255) NOT NULL,
    option_c         VARCHAR(255) NOT NULL,
    option_d         VARCHAR(255) NOT NULL,
    correct_option   ENUM('A','B','C','D') NOT NULL,
    difficulty_level ENUM('Easy','Medium','Hard') NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);


CREATE TABLE quiz_attempts (
    id                       INT AUTO_INCREMENT PRIMARY KEY,
    user_id                  INT NOT NULL,
    quiz_id                  INT NOT NULL,
    total_questions          INT NOT NULL,
    correct_answers          INT NOT NULL,
    score_percent            DECIMAL(5,2) NOT NULL,
    avg_answer_time_seconds  DECIMAL(6,2) NOT NULL,
    attempt_number           INT NOT NULL DEFAULT 1,
    previous_difficulty      ENUM('Easy','Medium','Hard') NULL,
    predicted_next_difficulty ENUM('Easy','Medium','Hard') NULL,
    attempted_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);


CREATE TABLE ml_predictions (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    user_id            INT NOT NULL,
    quiz_attempt_id    INT NOT NULL,
    predicted_difficulty ENUM('Easy','Medium','Hard') NOT NULL,
    model_used         VARCHAR(50) NOT NULL,   
    confidence_score   DECIMAL(5,4) NULL,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE
);


CREATE TABLE chatbot_logs (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    lesson_id    INT NULL,
    question     TEXT NOT NULL,
    response     TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE SET NULL
);


CREATE TABLE recommendations (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    user_id               INT NOT NULL,
    recommended_course_id INT NOT NULL,
    reason                TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recommended_course_id) REFERENCES courses(id) ON DELETE CASCADE
);


CREATE INDEX idx_courses_category ON courses(category);
CREATE INDEX idx_lessons_course ON lessons(course_id);
CREATE INDEX idx_attempts_user ON quiz_attempts(user_id);
CREATE INDEX idx_attempts_quiz ON quiz_attempts(quiz_id);
CREATE INDEX idx_questions_quiz ON questions(quiz_id);
