DROP DATABASE IF EXISTS sankalp_java;
CREATE DATABASE sankalp_java CHARACTER SET utf8mb4;
USE sankalp_java;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash CHAR(64) NOT NULL,
    full_name VARCHAR(100) NOT NULL
);
CREATE TABLE checkins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    checkin_date DATE NOT NULL,
    mood TINYINT NOT NULL CHECK (mood BETWEEN 1 AND 5),
    energy TINYINT NOT NULL CHECK (energy BETWEEN 1 AND 5),
    note VARCHAR(500),
    UNIQUE (user_id, checkin_date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE habits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    UNIQUE (user_id, name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE habit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    habit_id INT NOT NULL,
    done_date DATE NOT NULL,
    UNIQUE (habit_id, done_date),
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
);
CREATE TABLE journal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    UNIQUE (user_id, name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE journal_tags (
    journal_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (journal_id, tag_id),
    FOREIGN KEY (journal_id) REFERENCES journal(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
INSERT INTO users (email, password_hash, full_name) VALUES ('demo@sankalp.app', SHA2('demo1234', 256), 'Demo User');
INSERT INTO checkins (user_id, checkin_date, mood, energy, note) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 4, 4, 'Good day, went for a walk'),
(1, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 5, 4, 'Great mood after the walk'),
(1, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 3, 3, 'Tired, lots of assignments'),
(1, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 4, 4, 'Calm morning'),
(1, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 2, 2, 'Bad sleep'),
(1, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 5, 5, 'Weekend with friends'),
(1, DATE_SUB(CURDATE(), INTERVAL 7 DAY), 4, 5, 'Productive'),
(1, DATE_SUB(CURDATE(), INTERVAL 8 DAY), 3, 3, 'Average day'),
(1, DATE_SUB(CURDATE(), INTERVAL 9 DAY), 4, 3, 'Okay'),
(1, DATE_SUB(CURDATE(), INTERVAL 10 DAY), 2, 2, 'Stressed about exams'),
(1, DATE_SUB(CURDATE(), INTERVAL 11 DAY), 5, 4, 'Exam went well'),
(1, DATE_SUB(CURDATE(), INTERVAL 12 DAY), 4, 4, 'Relaxed'),
(1, DATE_SUB(CURDATE(), INTERVAL 13 DAY), 3, 3, 'Meh'),
(1, DATE_SUB(CURDATE(), INTERVAL 14 DAY), 4, 4, 'Fine');
INSERT INTO habits (user_id, name) VALUES (1, 'Walk 20 minutes'), (1, 'Meditate'), (1, 'Read a book');
INSERT INTO habit_logs (habit_id, done_date) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 1 DAY)),
(1, DATE_SUB(CURDATE(), INTERVAL 2 DAY)),
(1, DATE_SUB(CURDATE(), INTERVAL 4 DAY)),
(1, DATE_SUB(CURDATE(), INTERVAL 6 DAY)),
(1, DATE_SUB(CURDATE(), INTERVAL 7 DAY)),
(1, DATE_SUB(CURDATE(), INTERVAL 9 DAY)),
(1, DATE_SUB(CURDATE(), INTERVAL 11 DAY)),
(1, DATE_SUB(CURDATE(), INTERVAL 12 DAY)),
(1, DATE_SUB(CURDATE(), INTERVAL 14 DAY)),
(2, DATE_SUB(CURDATE(), INTERVAL 1 DAY)),
(2, DATE_SUB(CURDATE(), INTERVAL 2 DAY)),
(2, DATE_SUB(CURDATE(), INTERVAL 3 DAY)),
(2, DATE_SUB(CURDATE(), INTERVAL 4 DAY)),
(3, DATE_SUB(CURDATE(), INTERVAL 2 DAY)),
(3, DATE_SUB(CURDATE(), INTERVAL 3 DAY)),
(3, DATE_SUB(CURDATE(), INTERVAL 5 DAY)),
(3, DATE_SUB(CURDATE(), INTERVAL 8 DAY));
INSERT INTO tags (user_id, name) VALUES (1, 'study'), (1, 'family'), (1, 'health');
INSERT INTO journal (user_id, title, content, created_at) VALUES
(1, 'Exam week', 'Studied a lot today. Felt stressed but a walk helped me reset.', DATE_SUB(NOW(), INTERVAL 10 DAY)),
(1, 'Weekend trip', 'Went out with family. Laughed a lot, felt really happy.', DATE_SUB(NOW(), INTERVAL 6 DAY)),
(1, 'Sleep problems', 'Could not sleep. Will try meditation before bed.', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(1, 'Small win', 'Finished my project report and started reading again.', DATE_SUB(NOW(), INTERVAL 1 DAY));
INSERT INTO journal_tags (journal_id, tag_id) VALUES (1, 1), (1, 3), (2, 2), (3, 3), (4, 1);
