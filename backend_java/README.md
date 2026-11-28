# Sankalp - Mood & Habit Tracker (Java, console)

A terminal application in plain Java (no framework) that stores its data in MySQL through JDBC.
Course: Programming in Java (25CSE0202).

## 1. Problem statement

People who try to build healthy routines rarely see *why* a day went well or badly. Moods, habits and thoughts
are scattered across notes apps and memory. Sankalp lets one user record a daily mood/energy check-in, tick
daily habits, and write tagged journal entries in one place, then shows simple patterns
(for example: "average mood on the days I walked").

**Users:** students and individuals who want a lightweight self-tracking tool.

## 2. Objectives and scope

| Objective | Measurable outcome |
|---|---|
| Secure accounts | Register / login, passwords stored only as SHA-256 hashes |
| Daily check-in | One mood + energy (1-5) per day; saving twice updates the same row |
| Habit tracking | Tick/untick today, streak counted in days |
| Journal with tags | Write, search, read, delete entries; many-to-many tags |
| Insights | Report: 30-day averages, mood per habit, entries this month |
| Data in/out | Import check-ins from CSV, export journal to a text file |

**Out of scope:** graphical interface, web/mobile app, multi-device sync, AI features.

## 3. Design

Layers (Main never contains SQL, DAOs never read the keyboard):

```
Keyboard -> util.Input -> Main (menu) -> dao.*Dao -> JDBC -> MySQL (sankalp_java)
                                                  |
                                      returns model objects (User, Habit, CheckIn, Tag, JournalEntry)
```

```
src/
  Main.java                       menu and program flow
  com/model/  Showable, Entity, User, CheckIn, Habit, Tag, JournalEntry   (data classes)
  com/dao/    User/CheckIn/Habit/Journal/Tag/ReportDao                    (all SQL / JDBC)
  com/util/   Db (connection), Input (BufferedReader), AppException
database/     schema.sql                      7 tables + demo data
lib/          mysql-connector-j-8.3.0.jar     JDBC driver
docs/         STUDY_NOTES.md, presentation
```

Data model: `users` 1-N `checkins`, `habits`, `journal`, `tags`; `habits` 1-N `habit_logs`;
`journal` N-M `tags` through `journal_tags`. Every foreign key uses `ON DELETE CASCADE`.

## 4. Java concepts used

| Concept | Where |
|---|---|
| Interface, abstract class, inheritance, polymorphism | `Showable`, `Entity`, the model classes (`show()`) |
| Encapsulation | private fields with getters/setters |
| Collections | `ArrayList<Habit>`, `ArrayList<JournalEntry>` ... |
| Exception handling | custom `AppException`, `SQLException`, `IOException` caught in `Main` |
| JDBC | `Connection`, `PreparedStatement`, `ResultSet` in every dao |
| File I/O (buffering) | `BufferedReader` (keyboard, CSV import), `BufferedWriter` (journal export) |
| Packages | `com.dao`, `com.model`, `com.util` |

## 5. Setup and run

Requirements: JDK 17+, MySQL 8 running.

1. Create the database and demo data (also resets it any time):
   `mysql -u root -p < database/schema.sql`
2. Open `src/com/util/Db.java` and put your MySQL password in `PASSWORD`.
3. Run `run.bat` (Windows). Manual commands:
   ```
   javac -cp "lib/*" -d out src/Main.java src/com/dao/*.java src/com/model/*.java src/com/util/*.java
   java -cp "out;lib/*" Main
   ```
   On Mac/Linux use `:` instead of `;` in the classpath.
4. Log in with `demo@sankalp.app` / `demo1234`, or register a new user.

## 6. Current status

Done and tested: register/login, check-ins (+ CSV import), habits with streaks, journal with tags,
search and export, tag list/delete, report.

Pending / ideas: edit a journal entry, weekly summary, input validation for CSV lines,
moving the DB password to a config file.

## 7. More

`docs/STUDY_NOTES.md` explains every class, every SQL statement and likely viva questions.
