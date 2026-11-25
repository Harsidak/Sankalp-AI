-- SANKALP (console version) : database script.
-- Run it once (and again any time you want a fresh start before a demo):
--   mysql -u root -p < schema.sql
--
-- It deletes and recreates its OWN database "sankalp_java", so it never touches other databases.

DROP DATABASE IF EXISTS sankalp_java;
CREATE DATABASE sankalp_java CHARACTER SET utf8mb4;
USE sankalp_java;

-- ------------------------------------------------------------------
-- TABLES
-- PRIMARY KEY  = identifies one row.      AUTO_INCREMENT = MySQL numbers rows 1, 2, 3...
-- FOREIGN KEY  = points to a row in another table.
-- ON DELETE CASCADE = when the parent row is deleted, its children are deleted automatically.
-- UNIQUE       = the database refuses duplicates.
-- ------------------------------------------------------------------

CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash CHAR(64)     NOT NULL,          -- SHA2(password, 256) always gives 64 hex characters
    full_name     VARCHAR(100) NOT NULL
);

-- One mood/energy check-in per user per day.
CREATE TABLE checkins (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT          NOT NULL,
    checkin_date DATE         NOT NULL,
    mood         TINYINT      NOT NULL CHECK (mood BETWEEN 1 AND 5),
    energy       TINYINT      NOT NULL CHECK (energy BETWEEN 1 AND 5),
    note         VARCHAR(500),
    UNIQUE (user_id, checkin_date),               -- "one per day" is enforced HERE, not in Java
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE habits (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT          NOT NULL,
    name    VARCHAR(100) NOT NULL,
    UNIQUE (user_id, name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- A row here = "this habit was done on this day". Tick = INSERT, untick = DELETE.
CREATE TABLE habit_logs (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    habit_id  INT  NOT NULL,
    done_date DATE NOT NULL,
    UNIQUE (habit_id, done_date),
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
);

CREATE TABLE journal_entries (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    title      VARCHAR(200) NOT NULL,
    content    TEXT         NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE tags (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT         NOT NULL,
    name    VARCHAR(50) NOT NULL,
    UNIQUE (user_id, name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Many-to-many: one entry can have many tags, one tag can be on many entries.
-- A join table with two foreign keys solves it. The pair (entry_id, tag_id) is the primary key,
-- so the same tag cannot be attached to the same entry twice.
CREATE TABLE entry_tags (
    entry_id INT NOT NULL,
    tag_id   INT NOT NULL,
    PRIMARY KEY (entry_id, tag_id),
    FOREIGN KEY (entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)   REFERENCES tags(id)            ON DELETE CASCADE
);

-- ------------------------------------------------------------------
-- DEMO DATA  (login: demo@sankalp.app / demo1234)
-- Dates are written relative to today, so the demo always looks fresh.
-- Today and nothing earlier than yesterday is filled in, so you can check in live.
-- ------------------------------------------------------------------

INSERT INTO users (email, password_hash, full_name)
VALUES ('demo@sankalp.app', SHA2('demo1234', 256), 'Demo User');

-- 14 days of check-ins: yesterday (1 day ago) back to 14 days ago.
INSERT INTO checkins (user_id, checkin_date, mood, energy, note) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 1 DAY),  4, 4, 'Good day, went for a walk'),
(1, DATE_SUB(CURDATE(), INTERVAL 2 DAY),  5, 4, 'Great mood after the walk'),
(1, DATE_SUB(CURDATE(), INTERVAL 3 DAY),  3, 3, 'Tired, lots of assignments'),
(1, DATE_SUB(CURDATE(), INTERVAL 4 DAY),  4, 4, 'Calm morning'),
(1, DATE_SUB(CURDATE(), INTERVAL 5 DAY),  2, 2, 'Bad sleep'),
(1, DATE_SUB(CURDATE(), INTERVAL 6 DAY),  5, 5, 'Weekend with friends'),
(1, DATE_SUB(CURDATE(), INTERVAL 7 DAY),  4, 5, 'Productive'),
(1, DATE_SUB(CURDATE(), INTERVAL 8 DAY),  3, 3, 'Average day'),
(1, DATE_SUB(CURDATE(), INTERVAL 9 DAY),  4, 3, 'Okay'),
(1, DATE_SUB(CURDATE(), INTERVAL 10 DAY), 2, 2, 'Stressed about exams'),
(1, DATE_SUB(CURDATE(), INTERVAL 11 DAY), 5, 4, 'Exam went well'),
(1, DATE_SUB(CURDATE(), INTERVAL 12 DAY), 4, 4, 'Relaxed'),
(1, DATE_SUB(CURDATE(), INTERVAL 13 DAY), 3, 3, 'Meh'),
(1, DATE_SUB(CURDATE(), INTERVAL 14 DAY), 4, 4, 'Fine');

INSERT INTO habits (user_id, name) VALUES
(1, 'Walk 20 minutes'),   -- id 1
(1, 'Meditate'),          -- id 2
(1, 'Read a book');       -- id 3

-- Walking was done on the good-mood days, so the report shows a visible pattern.
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

INSERT INTO tags (user_id, name) VALUES
(1, 'study'),    -- id 1
(1, 'family'),   -- id 2
(1, 'health');   -- id 3

INSERT INTO journal_entries (user_id, title, content, created_at) VALUES
(1, 'Exam week',      'Studied a lot today. Felt stressed but a walk helped me reset.', DATE_SUB(NOW(), INTERVAL 10 DAY)),
(1, 'Weekend trip',   'Went out with family. Laughed a lot, felt really happy.',        DATE_SUB(NOW(), INTERVAL 6 DAY)),
(1, 'Sleep problems', 'Could not sleep. Will try meditation before bed.',               DATE_SUB(NOW(), INTERVAL 5 DAY)),
(1, 'Small win',      'Finished my project report and started reading again.',          DATE_SUB(NOW(), INTERVAL 1 DAY));

INSERT INTO entry_tags (entry_id, tag_id) VALUES
(1, 1), (1, 3),
(2, 2),
(3, 3),
(4, 1);
