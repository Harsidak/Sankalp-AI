# SANKALP (Java console version) – Study Notes

Read this top to bottom once, then use it as a reference. Everything here is about the **files in this folder**.
Nothing here needs anything outside the syllabus: classes, objects, inheritance, interfaces, exceptions, streams/buffers, JDBC and SQL.

- [1. The project in 30 seconds](#1-the-project-in-30-seconds)
- [2. Big picture and file map](#2-big-picture-and-file-map)
- [3. First principles: why is it built this way?](#3-first-principles-why-is-it-built-this-way)
- [4. The database](#4-the-database)
- [5. Every SQL statement explained](#5-every-sql-statement-explained)
- [6. JDBC step by step](#6-jdbc-step-by-step)
- [7. Java concepts and where they appear](#7-java-concepts-and-where-they-appear)
- [8. Streams and buffering](#8-streams-and-buffering)
- [9. One menu action, traced from keyboard to database](#9-one-menu-action-traced-from-keyboard-to-database)
- [10. File by file walkthrough](#10-file-by-file-walkthrough)
- [11. Questions the teacher can ask (with answers)](#11-questions-the-teacher-can-ask-with-answers)
- [12. Honest limitations (say them before he finds them)](#12-honest-limitations)
- [13. Splitting the explanation between teammates](#13-splitting-the-explanation-between-teammates)
- [14. Running it (short version)](#14-running-it-short-version)

---

## 1. The project in 30 seconds

> "Sankalp is a wellness tracker that runs in the terminal. A user registers, logs in, records a daily mood and energy
> check-in, ticks habits like 'Walk 20 minutes', and writes journal entries with tags. Everything is stored in a MySQL
> database that we reach from Java using JDBC. A report uses SQL to show, for example, what mood the user had on the days
> they did each habit. We can also import check-ins from a CSV file and export the journal to a text file."

**Where it comes from:** our team first built this as a web app (Python backend + React frontend). For the Java course
we rebuilt the same idea as a plain Java console program with MySQL, using only what the course teaches.

**What you are demonstrating:** OOP in Java + Java talking to a database + file input/output.

---

## 2. Big picture and file map

```
 keyboard                                             MySQL database
    |                                                  "sankalp_java"
    v                                                       ^
 Input.java  --->  Main.java (menu)  --->  XxxManager.java  |
 (BufferedReader)  asks + prints          (SQL lives here)  |
                                              |             |
                                              +--- JDBC ----+      Db.java gives the Connection
                                              |
                                  returns objects: User, Habit, CheckIn, Tag, JournalEntry
```

The rule: **Main never contains SQL. Managers never talk to the keyboard** (they receive values as parameters).
That is the only design rule in the project, and it keeps each file small.

| File | What it is | One-line purpose |
|---|---|---|
| `schema.sql` | SQL script | Creates the database, 7 tables, and demo data |
| `src/Main.java` | Class with `main` | The menu; calls managers; catches errors and prints them |
| `src/Input.java` | Helper | Reads typed text/numbers using `BufferedReader` |
| `src/Db.java` | Helper | Opens the MySQL connection (URL, user, password) |
| `src/Showable.java` | Interface | Promise: "I have a `show()` method" |
| `src/Entity.java` | Abstract class | Parent of all row-classes; stores the `id` |
| `src/User.java` `CheckIn.java` `Habit.java` `Tag.java` `JournalEntry.java` | Classes | One object = one row of a table |
| `src/AppException.java` | Custom exception | For user mistakes ("no habit with that number") |
| `src/UserManager.java` | Manager | register, login |
| `src/CheckInManager.java` | Manager | save today, list last N days, import CSV |
| `src/HabitManager.java` | Manager | add, delete, list with streaks, tick/untick |
| `src/JournalManager.java` | Manager | add (with tags), list/search, read, delete, export |
| `src/TagManager.java` | Manager | list with counts, delete |
| `src/ReportManager.java` | Manager | the 3-part report |
| `sample_checkins.csv` | Data | Example file for the CSV import |
| `lib/mysql-connector-j-8.3.0.jar` | Library | The JDBC **driver** (see section 6) |
| `run.bat` | Script | Compile + run in one command |

---

## 3. First principles: why is it built this way?

**Why a database and not just variables or a text file?**
Variables disappear when the program ends. A text file survives, but searching it, preventing duplicates, linking
"this entry has these tags", and answering "average mood on days I walked" would all need a lot of hand-written code.
A database does storage, searching, rules and calculations for us. Java only has to *ask*.

**Why does Java need JDBC?**
Java and MySQL are two separate programs. JDBC (Java Database Connectivity) is the standard set of Java classes
(`Connection`, `PreparedStatement`, `ResultSet`) for sending SQL text to a database and reading the answer.
A *driver* (the jar in `lib/`) is the translator that knows MySQL's specific language on the wire.

**Why classes like `Habit` and `Tag`?**
A row from the database is just loose values (`3, "Walk", 0, 2`). An object bundles them together with behaviour
(`habit.show()`). Main can then say "show this habit" instead of juggling separate variables.

**Why are there `Manager` classes?**
Each table (or group of tables) gets one class that owns its SQL. If a habit query is wrong you open `HabitManager`
and nowhere else. It also lets the work be split between teammates.

**Why inheritance (`Entity`)?**
Every row has an `id`. Writing `private int id` and `getId()` in five classes is repetition; we write it once in the parent.

**Why an interface (`Showable`)?**
It guarantees every thing we print has a `show()` method. Entity implements it, so all five row-classes must provide it.

**Why does the database enforce rules (UNIQUE, FOREIGN KEY, CHECK) instead of Java?**
Java code can have bugs or be bypassed; the database is the last line of defence and cannot be forgotten.
Example: "one check-in per user per day" is `UNIQUE (user_id, checkin_date)` in `schema.sql`; even if Java forgot
to check, MySQL refuses the second row.

**Why `PreparedStatement` with `?` and not string joining?**
If we wrote `"... WHERE email = '" + email + "'"`, a user typing `' OR '1'='1` could change the meaning of the SQL
(**SQL injection**). With `?`, the value is sent separately and is always treated as data, never as SQL.

---

## 4. The database

Database name: `sankalp_java` (created by `schema.sql`; running the script again wipes and rebuilds it – handy before a demo).

### 4.1 Entity-relationship diagram

```
                           +----------+
                           |  users   |
                           | id (PK)  |
                           | email  U |
                           | password_hash
                           | full_name|
                           +----+-----+
        1 user has many        |
   +-------------+-------------+--------------+--------------+
   |             |                            |              |
   v             v                            v              v
+----------+ +---------+               +----------------+ +--------+
| checkins | | habits  |               | journal_entries| |  tags  |
| id  (PK) | | id (PK) |               | id (PK)        | | id (PK)|
| user_id  | | user_id |               | user_id (FK)   | | user_id|
| date     | | name    |               | title, content | | name   |
| mood     | +----+----+               | created_at     | +---+----+
| energy   |      | 1 habit has many   +--------+-------+     |
| note     |      v                             |             |
+----------+ +------------+                     |  many-to-many
 UNIQUE      | habit_logs |                     v             |
 (user,date) | id (PK)    |                +-------------+     |
             | habit_id   |                | entry_tags  |<----+
             | done_date  |                | entry_id (PK,FK)
             +------------+                | tag_id   (PK,FK)
              UNIQUE(habit,date)           +-------------+
```
(PK = primary key, FK = foreign key, U = unique.)

### 4.2 The tables, one by one

| Table | Meaning of one row | Key rules and why |
|---|---|---|
| `users` | One account | `email` UNIQUE – two accounts cannot share an email. `password_hash` is 64 chars: the SHA-256 scramble of the password. |
| `checkins` | How user X felt on day D | `UNIQUE(user_id, checkin_date)` – one per day. `CHECK (mood BETWEEN 1 AND 5)` – the DB rejects 9. |
| `habits` | A habit the user wants to track | `UNIQUE(user_id, name)` – no duplicate habit names for one user. |
| `habit_logs` | "Habit H was done on day D" | A row **exists** = done. Tick = INSERT, untick = DELETE. `UNIQUE(habit_id, done_date)` – can't be done twice in a day. |
| `journal_entries` | One diary entry | `created_at` has `DEFAULT CURRENT_TIMESTAMP` – MySQL fills the time automatically. |
| `tags` | A label like "study" | `UNIQUE(user_id, name)` – a user has each tag name once; two users can both have "study". |
| `entry_tags` | "Entry E has tag T" | Join table; **primary key is the pair** `(entry_id, tag_id)`, so the same tag can't be attached twice. |

### 4.3 Ideas you must be able to explain

- **Primary key (PK):** the column(s) that identify a row uniquely. `AUTO_INCREMENT` makes MySQL hand out 1, 2, 3...
- **Foreign key (FK):** a column that must match an existing PK in another table (`checkins.user_id → users.id`).
  You cannot add a check-in for a user that does not exist.
- **`ON DELETE CASCADE`:** if the parent row is deleted, the children are deleted automatically.
  Delete a habit → its `habit_logs` go. Delete a tag → its rows in `entry_tags` go (the entries stay).
  Delete a user → everything of theirs goes.
- **UNIQUE:** the database refuses a second row with the same value (or the same combination, for a composite UNIQUE).
- **Many-to-many:** one entry has many tags AND one tag is on many entries. You cannot store that in one column cleanly,
  so you add a **third table** (`entry_tags`) holding pairs. That is the standard solution.
- **One-to-many:** one user → many check-ins. Solved by putting the `user_id` foreign key on the "many" side.
- **Normalization (simple version):** each fact is stored once. The tag's name lives in `tags` only; entries refer to
  it by id. If a tag is renamed, one row changes, not hundreds. (This is "avoid redundancy / update anomalies".)
- **Why is `habit_logs` a table and not a column on `habits`?** A habit has many completion days; a single column can't
  hold a growing list without breaking First Normal Form (one value per cell).
- **Why `password_hash` and not `password`?** If the database leaks, plain passwords are exposed. A hash is a one-way
  scramble: same input → same output, but you cannot get the password back. At login we scramble what was typed and compare.
- **Index:** the UNIQUE constraints automatically create indexes (fast lookup structures), so searching by
  `(user_id, checkin_date)` is fast.
- **InnoDB:** the MySQL storage engine that supports foreign keys and transactions (it's the default in MySQL 8).

---

## 5. Every SQL statement explained

### In `UserManager`
```sql
INSERT INTO users (email, password_hash, full_name) VALUES (?, SHA2(?, 256), ?)
```
Adds a user. `SHA2(?,256)` is a MySQL function that scrambles the password with SHA-256. Each `?` is filled by `ps.setString(...)`.
Duplicate email → MySQL throws error 1062 (Duplicate entry) → Java gets a `SQLException`.

```sql
SELECT id, email, full_name FROM users WHERE email = ? AND password_hash = SHA2(?, 256)
```
Login: scramble the typed password the same way and look for a row where both match. No row → wrong login (we return `null`).

### In `CheckInManager`
```sql
INSERT INTO checkins (user_id, checkin_date, mood, energy, note) VALUES (?, CURDATE(), ?, ?, ?)
ON DUPLICATE KEY UPDATE mood = ?, energy = ?, note = ?
```
`CURDATE()` = today's date (from MySQL). Normally INSERT. But if today already has a row for this user, the UNIQUE rule
would be broken → instead of an error, `ON DUPLICATE KEY UPDATE` changes the existing row. So "check in twice" = "edit today's".
That's why 7 parameters are set: 4 for the insert, 3 for the update.

```sql
SELECT id, checkin_date, mood, energy, note FROM checkins
WHERE user_id = ? AND checkin_date >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
ORDER BY checkin_date DESC
```
Last N days, newest first. `DATE_SUB(CURDATE(), INTERVAL 14 DAY)` = the date 14 days ago.

### In `HabitManager`
```sql
SELECT id, name FROM habits WHERE user_id = ? ORDER BY id
```
All habits of this user (the `WHERE user_id = ?` is why users never see each other's data).

```sql
SELECT COUNT(*) FROM habit_logs WHERE habit_id = ? AND done_date = DATE_SUB(CURDATE(), INTERVAL ? DAY)
```
"Was it done N days ago?" (0 = today). COUNT is 0 or 1 (UNIQUE guarantees never more).

```sql
INSERT INTO habit_logs (habit_id, done_date) VALUES (?, CURDATE())     -- tick
DELETE FROM habit_logs WHERE habit_id = ? AND done_date = CURDATE()    -- untick
```
```sql
DELETE FROM habits WHERE id = ? AND user_id = ?
```
`AND user_id = ?` stops a user deleting someone else's habit. `executeUpdate()` returns the number of rows deleted;
0 means "not found / not yours" → we throw `AppException`.

**Streak logic (Java, not SQL):** start at today (or yesterday if today isn't ticked yet) and keep asking "done N days ago?"
while the answer is yes, counting. It stops at the first gap. Example: done yesterday and the day before, not today → streak 2.

### In `TagManager`
```sql
SELECT t.id, t.name, COUNT(et.entry_id) AS entry_count
FROM tags t LEFT JOIN entry_tags et ON et.tag_id = t.id
WHERE t.user_id = ? GROUP BY t.id, t.name ORDER BY t.name
```
- `t` and `et` are short **aliases** for the table names.
- **LEFT JOIN:** keep every tag even if no entry uses it (count 0). A plain (INNER) JOIN would drop unused tags.
- `COUNT(et.entry_id)` counts only non-NULL values, so unused tags correctly give 0.
- **GROUP BY:** collapse the many joined rows into one row per tag so COUNT works per tag.

### In `JournalManager`
```sql
INSERT INTO journal_entries (user_id, title, content) VALUES (?, ?, ?)
```
`created_at` is not listed, so MySQL fills it with the default. `RETURN_GENERATED_KEYS` + `getGeneratedKeys()` gives us the new `id`.

Attaching a tag (3 statements):
```sql
INSERT IGNORE INTO tags (user_id, name) VALUES (?, ?)         -- create the tag if it doesn't exist
SELECT id FROM tags WHERE user_id = ? AND name = ?            -- get its id (new or old)
INSERT IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?, ?) -- link entry <-> tag
```
`INSERT IGNORE` = "if this would break a UNIQUE/PRIMARY KEY rule, skip silently instead of raising an error".

```sql
SELECT e.id, e.title, e.content, e.created_at, GROUP_CONCAT(t.name SEPARATOR ', ') AS tags
FROM journal_entries e
LEFT JOIN entry_tags et ON et.entry_id = e.id
LEFT JOIN tags t ON t.id = et.tag_id
WHERE e.user_id = ? AND (e.title LIKE ? OR e.content LIKE ?)
GROUP BY e.id ORDER BY e.created_at DESC
```
The most important query. Read it as: entries → (via the join table) → their tags → one row per entry, tag names glued into one text.
`LIKE '%walk%'` matches any text *containing* "walk" (`%` = any characters). With an empty search the pattern is `%%`, which matches everything,
so one query serves both "list all" and "search". `GROUP_CONCAT` joins the several tag names of one entry into `study, health`.
Entries with no tags give `NULL`, which Java turns into `""`.

### In `ReportManager`
1. `SELECT COUNT(*), AVG(mood), AVG(energy) ... WHERE ... last 30 days` – **aggregate functions** over many rows → a single row.
2. The 3-table join:
```sql
FROM habits h
JOIN habit_logs l ON l.habit_id = h.id
JOIN checkins c  ON c.user_id = h.user_id AND c.checkin_date = l.done_date
WHERE h.user_id = ? GROUP BY h.id, h.name ORDER BY avg_mood DESC
```
For each day a habit was done (`habit_logs`), find the check-in of that same day (`checkins`), then average the mood per habit.
This is the "insight": walking days have mood 4.33 vs the overall 3.83.
3. `COUNT(*)` of entries where `YEAR(created_at)` and `MONTH(created_at)` equal today's – entries this month.

### JOIN cheat-sheet
| Join | Keeps |
|---|---|
| `JOIN` (INNER) | Only rows that have a match on both sides |
| `LEFT JOIN` | All rows of the left table, even without a match (missing side = NULL) |

---

## 6. JDBC step by step

```java
Connection con = Db.connect();                       // 1. open the line to MySQL
PreparedStatement ps = con.prepareStatement(sql);    // 2. send the SQL text (with ?) to be prepared
ps.setInt(1, userId);                                // 3. fill the 1st ?  (numbering starts at 1, not 0)
ResultSet rs = ps.executeQuery();                    // 4. run a SELECT
while (rs.next()) {                                  // 5. move to the next row; false when no more rows
    rs.getString("name");                            // 6. read a column of the current row
}
rs.close(); ps.close();                              // 7. release resources
con.close();                                         // 8. close the connection (end of Main)
```

| Term | Meaning |
|---|---|
| `Connection` | The open line between Java and MySQL (like a phone call). One is made in `Main` and shared. |
| `DriverManager.getConnection(url, user, password)` | Opens it. The driver jar in `lib/` is found through the classpath. |
| URL `jdbc:mysql://localhost:3306/sankalp_java` | protocol : host : port (3306 = MySQL's default) / database name |
| `useSSL=false&allowPublicKeyRetrieval=true` | Settings so a plain local MySQL accepts the login without certificates. Only for local use. |
| `PreparedStatement` | SQL with `?` slots. Safer (no injection) and the database can reuse the parsed query. |
| `executeQuery()` | For `SELECT`; returns a `ResultSet` (a table of rows you walk through). |
| `executeUpdate()` | For `INSERT/UPDATE/DELETE`; returns how many rows changed. |
| `ResultSet` | Has a cursor that starts *before* the first row; `next()` moves it. |
| `SQLException` | Anything going wrong in the database (bad SQL, duplicate key, connection lost). |
| Driver | The jar `mysql-connector-j`. Java's JDBC classes are generic; the driver implements them for MySQL. |

**Why close things?** Each open statement/result holds memory and a server-side resource. We close them as soon as we are done.
(If an error is thrown halfway, the statements are cleaned up when `con.close()` runs at the end of the program.
Writing `try/finally` around each one would be the next step; we kept the code simpler on purpose.)

**Transactions:** by default JDBC runs in *auto-commit* mode – every statement is saved immediately. We did not need
multi-statement transactions. (If asked: `con.setAutoCommit(false)` … `con.commit()` / `con.rollback()` would make a group of
statements all-or-nothing, e.g. adding an entry *and* its tags.)

---

## 7. Java concepts and where they appear

| Concept | Where | Short explanation |
|---|---|---|
| **Class / object** | `Habit h = new Habit(1, "Walk")` | A class is a blueprint, an object is one thing built from it. |
| **Encapsulation** | `private int id;` + `getId()` in `Entity` | Fields are hidden; the outside world uses methods. Protects data from accidental change. |
| **Constructor** | `public Habit(int id, String name)` | Runs on `new`; sets up the object. |
| **`this`** | `this.name = name;` | Refers to the current object; separates the field from the parameter with the same name. |
| **Inheritance** | `class Habit extends Entity` | Habit *is an* Entity and gets its `id` and `getId()`. |
| **`super(id)`** | first line of every child constructor | Calls the parent's constructor. |
| **Abstract class** | `abstract class Entity` | Cannot be instantiated (`new Entity()` is an error); exists to be extended. |
| **Interface** | `interface Showable { void show(); }` | Only a contract of methods. A class `implements` it and must supply them. |
| **Method overriding** | `@Override public void show()` in each class | The child replaces the parent's/interface's method with its own version. |
| **Polymorphism** | Any `Entity`/`Showable` can be asked to `show()` | Same call, different behaviour per class. Our lists call `h.show()`, `t.show()`, `c.show()`. |
| **Custom exception** | `class AppException extends Exception` | Our own error type for user mistakes. |
| **throw / throws** | `throw new AppException("...")`, `throws SQLException` | `throw` raises an error; `throws` in a method header says "this method may raise it, the caller must handle it". |
| **try / catch** | in `Main` (menu loop) and `Input.number` | Run risky code; if it fails, jump to the matching `catch` instead of crashing. |
| **Checked exceptions** | `SQLException`, `IOException`, `AppException` | The compiler forces you to catch or declare them. |
| **Collections** | `ArrayList<Habit>` | A growing list. `<Habit>` = it holds only Habits. |
| **for-each loop** | `for (Habit h : habits.list(id))` | "For every habit in the list". |
| **switch** | the menu in `Main` | Picks a block by number; `break` ends each case; `default` handles anything else. |
| **static** | `Input.text(...)`, `Db.connect()` | Belongs to the class, not an object: call it without `new`. |
| **Ternary operator** | `doneToday ? "[x]" : "[ ]"` | Short if-else that gives a value. |
| **String methods** | `trim()`, `split(",")`, `toLowerCase()`, `isEmpty()` | Clean and cut text. |
| **File I/O** | `FileReader`, `FileWriter` + buffers | See section 8. |

**Why `Main` methods say `throws Exception`:** `Exception` is the parent of all exceptions (`SQLException`, `IOException`...),
so it says "anything can go wrong in here". The real handling is in the menu loop's `catch` blocks.

**What `@Override` does:** a label that tells the compiler "I mean to replace a parent method". If the name was mistyped, the compiler complains.

---

## 8. Streams and buffering

A **stream** is a flow of data: bytes or characters moving from a source to a destination.
A **buffer** is a small chunk of memory that collects data so we read/write in bigger pieces instead of one character at a time (much faster, because every real read/write to a disk or keyboard is slow).

**Reading from the keyboard (`Input.java`):**
```java
new BufferedReader(new InputStreamReader(System.in))
```
`System.in` (bytes) → `InputStreamReader` (bytes → characters) → `BufferedReader` (collects characters, gives whole lines with `readLine()`).
Each wrapper adds one ability; this layering is the **decorator** idea.

**Reading a CSV file (`CheckInManager.importCsv`):**
```java
new BufferedReader(new FileReader(fileName))
while ((line = reader.readLine()) != null) { ... }
```
`FileReader` opens the file as characters; `BufferedReader` gives lines; `readLine()` returns `null` at the end of the file.
Each line `2026-11-20,4,3,felt fine` is cut with `split(",", 4)`; the `4` means "at most 4 pieces", so commas inside the note stay in the note.

**Writing to a file (`JournalManager.exportToFile`):**
```java
new BufferedWriter(new FileWriter(fileName))
writer.write(...); writer.newLine(); ... writer.close();
```
Text goes into the buffer first; `close()` flushes (empties) the buffer into the file. Forgetting `close()` can lose the last text.
Result: `journal_export.txt` in the project folder (git-ignored).

**Scanner vs BufferedReader:** Scanner parses numbers/words for you but is slower and trickier with mixed `nextInt()`/`nextLine()`.
BufferedReader reads whole lines, and we convert with `Integer.parseInt` ourselves – more transparent and in line with "buffering".

**Byte stream vs character stream:** `InputStream/OutputStream` move raw bytes; `Reader/Writer` move characters (text, with encoding).
We use character streams because we handle text.

---

## 9. One menu action, traced from keyboard to database

User picks **5 – Tick / untick a habit** and types habit number **1**.

1. `Main.mainMenu` reads `5` with `Input.number("Choose: ")` → `reader.readLine()` → `Integer.parseInt` → `switch` jumps to `case 5`.
2. `case 5` asks `Input.number("Habit number: ")` → 1, then calls `habits.toggleToday(userId, 1)`.
3. `HabitManager.toggleToday`:
   a. `SELECT COUNT(*) FROM habits WHERE id=1 AND user_id=?` – does this habit exist **and belong to this user**? If 0 → `throw new AppException(...)`.
   b. `isDone(1, 0)` → `SELECT COUNT(*) FROM habit_logs WHERE habit_id=1 AND done_date = today`.
   c. If done → `DELETE FROM habit_logs ...` (untick), else `INSERT INTO habit_logs ...` (tick). Remember which one in `nowDone`.
   d. Returns `nowDone` to Main.
4. Main prints `Ticked for today.` or `Unticked.`.
5. If anything threw, the `catch` at the bottom of the menu loop prints `Problem: ...` and the menu comes back. The program never crashes.

Then **4 – Show habits** → `habits.list(userId)` → returns `ArrayList<Habit>` → Main calls `h.show()` on each, which prints `[x] Walk 20 minutes (streak: 3 days)`.

---

## 10. File by file walkthrough

**`Db.java`** – three constants (URL, USER, PASSWORD) and one method `connect()` that returns `DriverManager.getConnection(...)`.
You edit `PASSWORD` here. Nothing else in the project knows the password.

**`Input.java`** – two static methods. `text()` prints a question and returns the trimmed line. `number()` loops until `parseInt` succeeds
(the only place with a `NumberFormatException` catch, so typing "abc" doesn't crash).

**`Showable` → `Entity` → `User / CheckIn / Habit / Tag / JournalEntry`** – the object model.
`Showable` (interface: `show()`), `Entity` (abstract: `id`, `getId()`), each child adds its own fields, constructor (`super(id)` first) and `show()`.
`CheckIn.show()` builds a `####` bar with a loop. `Habit` has setters because `doneToday` and `streak` are calculated *after* the row is read.
`JournalEntry` has `show()` (one line) and `showFull()` (with content).

**`AppException`** – 3 lines. `extends Exception`; passes its message to the parent constructor with `super(message)`.

**`UserManager`** – `register` (INSERT with SHA2), `login` (SELECT, returns `User` or `null`).

**`CheckInManager`** – `saveToday` (validate 1–5 in Java, then upsert), `lastDays` (SELECT → `ArrayList<CheckIn>`), `importCsv` (file → loop → upsert per line).
The range check is in Java *and* in the table's `CHECK`, so there are two layers.

**`HabitManager`** – `add`, `delete`, `list` (+ calculates `doneToday` and `streak` for each), `toggleToday`, private `isDone`, private `streak`.

**`TagManager`** – `listWithCounts` (LEFT JOIN + GROUP BY) and `delete`.

**`JournalManager`** – `add` (insert, get new id, loop over tag names → `attachTag`), `list` (join query; also search), `get` (finds one entry in the list; throws if absent),
`delete`, `exportToFile`. Tag names are lowercased so "Study" and "study" are the same tag.

**`ReportManager`** – `print` runs the three queries and prints with `printf` (`%.2f` = 2 decimals, `%-20s` = left-aligned in 20 spaces, `%n` = newline).

**`Main`** – six manager fields; `main` opens the connection and creates the managers; `loginScreen` loops until a login succeeds or the user exits;
`mainMenu` prints the menu, reads a number, and runs a `switch`. Three `catch` blocks (`AppException`, `SQLException`, `IOException`) keep it alive.

---

## 11. Questions the teacher can ask (with answers)

Answers are written the way you would say them. Don't memorise word for word – understand the idea.

### A. About the project

**Q1. What does your project do?** → Section 1.

**Q2. Why did you choose this project?** → It shows several course topics together: OOP, exceptions, file streams, and JDBC with a real relational design (one-to-many and many-to-many).

**Q3. Who uses it?** → A person tracking mood, habits and a journal; each user's data is private (every query has `WHERE user_id = ?`).

**Q4. What is the flow of the program?** → `main` connects to the DB → login screen → main menu loop → each choice calls a manager → manager runs SQL → result printed → back to menu → exit closes the connection.

**Q5. Where is the frontend / website?** → That was the first version of the team's project (Python + React). For the Java course we built this console version of the same idea so everything uses Java and JDBC.

**Q6. Did you use AI / who wrote this?** → Be honest and calm: "We used AI as a helper while building, and then we studied every file; I can explain any line." (Your teacher already said this is acceptable as long as you can explain it.) Then prove it by explaining.

**Q7. What would you add next?** → Password rules, a GUI, edit entries, per-tag filtering, transactions around "add entry + tags", better closing with `try/finally`.

### B. OOP

**Q8. What is a class? An object?** → Class = blueprint (`Habit`). Object = one instance made with `new Habit(1,"Walk")`.

**Q9. Where did you use inheritance?** → `User, CheckIn, Habit, Tag, JournalEntry extends Entity`. Entity holds `id`.

**Q10. Why is `Entity` abstract?** → An "entity" alone means nothing; we only want specific kinds. `abstract` prevents `new Entity(...)`.

**Q11. What is an interface? Difference from an abstract class?** → An interface lists methods a class must have (`Showable.show()`); a class can implement many. An abstract class can also hold fields and finished methods (like `id`/`getId`) but a class can extend only one.

**Q12. Where is polymorphism?** → `show()` is declared once but each class prints differently; Main just calls `h.show()` / `t.show()`.

**Q13. What is method overriding? Overloading?** → Overriding: child redefines a parent/interface method with the same signature (`show()`). Overloading: same name, different parameters in one class (we don't use it).

**Q14. What is encapsulation?** → Hiding fields with `private` and exposing them via methods (`getId()`). Example: `Entity.id`.

**Q15. What does `super(id)` do?** → Calls the parent constructor so `Entity` stores the id. It must be the first line of a child constructor.

**Q16. What does `this` mean?** → The current object; `this.name = name` copies the parameter into the field.

**Q17. What is `static`?** → Belongs to the class, so `Input.text()` works without creating an `Input` object. `main` itself is static so Java can start without an object.

**Q18. Why `public static void main(String[] args)`?** → `public`: JVM can see it; `static`: callable without an object; `void`: returns nothing; `String[] args`: command-line arguments.

**Q19. What is `@Override`?** → Annotation telling the compiler we intend to override; it errors if the method does not really exist in the parent.

**Q20. Difference between `==` and `.equals()`?** → `==` compares numbers/primitives (and object references); `.equals()` compares the *content* of Strings. In our code we compare numbers with `==` (e.g. `entry.getId() == entryId`).

**Q21. Why `ArrayList` and not an array?** → Its size grows automatically; we don't know how many rows a query returns.

**Q22. What is a constructor?** → Special method with the class's name, no return type; runs on `new` to initialise fields.

**Q23. What are getters/setters for?** → Controlled access to private fields. `Habit` has setters for the two calculated values.

**Q24. What is a package / why none here?** → A package is a folder-namespace for classes. For a small project the default package keeps compiling to one command.

### C. Exceptions

**Q25. What is an exception?** → An object representing a problem at run time that interrupts normal flow.

**Q26. `throw` vs `throws`?** → `throw` actually raises one (`throw new AppException(...)`). `throws` in a method signature declares that the method may raise it.

**Q27. Checked vs unchecked?** → Checked (`SQLException`, `IOException`, our `AppException`): compiler forces handling. Unchecked (`NumberFormatException`, `NullPointerException`): not forced.

**Q28. Why did you make `AppException`?** → To separate *user mistakes* ("no habit with that number") from *database failures* (`SQLException`) and print different messages.

**Q29. What happens if I enter a letter where a number is expected?** → `Input.number` catches `NumberFormatException` and asks again.

**Q30. What if the CSV file does not exist?** → `FileReader` throws `FileNotFoundException` (a kind of `IOException`); Main's `catch (IOException e)` prints "File error: ..." and the menu continues.

**Q31. What if MySQL is off / wrong password?** → `Db.connect()` throws `SQLException` straight out of `main` and the program stops with the error message (we need the DB for anything to work).

**Q32. Why can there be several catch blocks?** → Each catches a different type and handles it differently.

**Q33. What is `finally`?** → Code that always runs after try/catch. We don't use it; we close resources directly after use (limitation, section 12).

### D. Streams and files

**Q34. What is a stream?** → A flow of data between a program and a source/destination (keyboard, file, network).

**Q35. Byte streams vs character streams?** → Bytes: `InputStream/OutputStream`; characters: `Reader/Writer`. We process text, so we use readers/writers.

**Q36. Why wrap `System.in` in `InputStreamReader` and `BufferedReader`?** → `System.in` gives bytes; `InputStreamReader` converts to characters; `BufferedReader` adds a buffer and `readLine()`.

**Q37. What is buffering and why use it?** → Collecting data in memory so we make fewer slow reads/writes. Reading 8 KB at once is faster than 8,192 single-character reads.

**Q38. What does `readLine()` return at the end of a file?** → `null`. That is why the loop is `while ((line = reader.readLine()) != null)`.

**Q39. Why `close()` the writer?** → It flushes the buffer and releases the file. Without it, text may never reach the file.

**Q40. What does `FileWriter(fileName)` do if the file already exists?** → It overwrites it (use `new FileWriter(name, true)` to append).

**Q41. Why did you split with `split(",", 4)`?** → A note can contain commas. The limit `4` produces at most four pieces, so everything after the third comma stays together as the note.

**Q42. Is `Scanner` better?** → Different trade-off; we used BufferedReader because the course covers buffering and it reads full lines predictably.

### E. JDBC

**Q43. What is JDBC?** → Java's standard API for talking to relational databases.

**Q44. What is a driver and where is it?** → The vendor-specific implementation (`lib/mysql-connector-j-8.3.0.jar`). Without it on the classpath, `getConnection` fails with "No suitable driver".

**Q45. Do you call `Class.forName(...)`?** → No. Since JDBC 4 the driver registers itself automatically when it is on the classpath.

**Q46. What is the classpath / what is `-cp "lib/*"`?** → The list of places where Java looks for classes. We add the `lib` folder so it finds the MySQL driver, and `out` for our own compiled classes.

**Q47. `Statement` vs `PreparedStatement`?** → `PreparedStatement` takes `?` parameters, prevents SQL injection, and the SQL is parsed once. We use it everywhere.

**Q48. What is SQL injection? Show an example.** → If SQL is built by joining strings, typing `' OR '1'='1` as the email turns the WHERE into something always true. With `?`, the text is just a value.

**Q49. `executeQuery` vs `executeUpdate`?** → Query for SELECT (returns ResultSet); Update for INSERT/UPDATE/DELETE (returns affected row count).

**Q50. What is a `ResultSet` and what does `next()` do?** → A table of rows with a cursor before the first row; `next()` advances and returns `false` when there are none.

**Q51. Why are parameter indexes 1-based?** → JDBC convention: the first `?` is 1.

**Q52. How do you get the id of a newly inserted row?** → Prepare with `Statement.RETURN_GENERATED_KEYS`, run, then `ps.getGeneratedKeys()`; `keys.next(); keys.getInt(1)`.

**Q53. What is auto-commit?** → Each statement is saved immediately. `con.setAutoCommit(false)` + `commit()/rollback()` makes groups atomic.

**Q54. Why one shared `Connection`?** → Opening connections is slow; a single user at a time means one is enough. (Real servers use a connection pool.)

**Q55. What if two things use the same connection?** → Fine here because the program is single-threaded and sequential.

**Q56. Where is the DB password?** → In `Db.java` as a constant for simplicity. In a real project it would be an environment variable or config file, never committed.

### F. SQL and DBMS

**Q57. What is a primary key?** → Column(s) uniquely identifying each row, never NULL.

**Q58. Foreign key?** → A column that must match a primary key in another table; enforces references.

**Q59. What does `ON DELETE CASCADE` do? Example.** → Deleting a parent deletes its children. Delete a habit → its logs go; delete a user → all their data goes.

**Q60. What is the difference between UNIQUE and PRIMARY KEY?** → Both forbid duplicates. A table has one primary key (no NULLs); it can have many UNIQUE constraints.

**Q61. Why `UNIQUE(user_id, checkin_date)` instead of just `UNIQUE(checkin_date)`?** → Different users may check in on the same date; the *pair* must be unique.

**Q62. How did you model many-to-many?** → `entry_tags` with two foreign keys; its primary key is the pair, so duplicates are impossible.

**Q63. What is normalization? Is your DB normalized?** → Organising tables so each fact is stored once. Yes: tag names are in `tags` only, completions in `habit_logs`, users referenced by id – no repeating groups, no copied values. (Roughly 3NF.)

**Q64. INNER JOIN vs LEFT JOIN? Where did you use each?** → Inner: only matches (the report's habit↔checkin join). Left: keep all left rows (tags with 0 entries; entries with no tags).

**Q65. What is `GROUP BY`?** → Groups rows with the same value so aggregates (COUNT, AVG) are computed per group.

**Q66. Aggregate functions you used?** → `COUNT`, `AVG`, and `GROUP_CONCAT` (MySQL-specific, glues text).

**Q67. `WHERE` vs `HAVING`?** → WHERE filters rows before grouping; HAVING filters groups after. We did not need HAVING.

**Q68. What does `LIKE '%x%'` mean?** → Text containing x anywhere; `%` matches any number of characters.

**Q69. What is `CURDATE()`? `NOW()`?** → Current date / current date and time on the DB server.

**Q70. Why store `SHA2` hashes?** → Passwords must not be readable. Hashing is one-way: we hash what the user types and compare hashes.

**Q71. Is SHA-256 enough for passwords?** → Honest answer: it's fine for a student project but real systems use salted, slow hashes (bcrypt/argon2) to resist brute force. We mention it as a limitation.

**Q72. What is `AUTO_INCREMENT`?** → MySQL automatically assigns the next number as id.

**Q73. What is `INSERT IGNORE`?** → An INSERT that skips rows violating UNIQUE/PRIMARY KEY instead of failing. We use it so adding an existing tag or link is harmless.

**Q74. What is `ON DUPLICATE KEY UPDATE`?** → "Insert, but if the key already exists, update that row instead" – gives upsert behaviour for the daily check-in.

**Q75. What is `CHECK (mood BETWEEN 1 AND 5)`?** → A rule the DB tests on every insert/update. (MySQL 8.0.16+ enforces it.)

**Q76. What is an index?** → A sorted structure that makes lookups fast. UNIQUE constraints create one automatically.

**Q77. What is a transaction? ACID?** → A group of statements that succeeds or fails as one. ACID = Atomicity, Consistency, Isolation, Durability. InnoDB supports it; we run in auto-commit.

**Q78. DDL vs DML?** → DDL defines structure (`CREATE TABLE`), DML works with data (`INSERT/SELECT/UPDATE/DELETE`). `schema.sql` has both.

**Q79. What are the data types you used?** → `INT`, `TINYINT` (small numbers 1–5), `VARCHAR(n)` (text up to n), `TEXT` (long text), `DATE`, `DATETIME`, `CHAR(64)` (fixed length for the hash).

**Q80. Why `VARCHAR` for names but `TEXT` for content?** → Names have a sensible limit; journal content can be long and has no fixed limit.

**Q81. What happens if I delete a user?** → Not in the menu, but `DELETE FROM users WHERE id=1` would cascade to check-ins, habits (and logs), entries (and their tag links) and tags.

**Q82. Can two users have the same tag name?** → Yes; uniqueness is per user.

**Q83. What if I try to insert a mood of 9?** → Java rejects it (`AppException`). Even if Java forgot, the `CHECK` constraint would reject it (`SQLException`).

**Q84. Why check in Java *and* in the table?** → Java gives a friendly message quickly; the DB is the unbreakable guarantee.

### G. Design choices

**Q85. Why one class per table group (managers)?** → Separation of concerns: menu code vs SQL code. Easier to read, test and share between teammates.

**Q86. Why do managers get the Connection through the constructor?** → One shared connection; the manager doesn't need to know the password or URL.

**Q87. Why return objects (`ArrayList<Habit>`) instead of printing in the manager?** → The manager gets data, Main decides how to display it. (ReportManager prints directly because a report *is* output.)

**Q88. Why are the streak calculations in Java, not SQL?** → Counting consecutive days is awkward in plain SQL; a small loop is easier to follow.

**Q89. Isn't streak slow (many queries)?** → Yes, one query per day checked. Fine for a student project with short streaks.

**Q90. Why seed data?** → So the demo and report show meaningful numbers immediately.

### H. "Point at any line" – examples

- `rs.next();` right after `executeQuery()` when we expect exactly one row (COUNT) → "A COUNT query always returns one row; `next()` moves the cursor onto it."
- `ps.setInt(1, userId);` → "Fills the first `?`."
- `return Integer.parseInt(line);` inside try → "Converts text to int; throws NumberFormatException if it isn't a number."
- `for (String name : names)` → "For every tag name in the array."
- `name = name.trim().toLowerCase();` → "Remove spaces and make lowercase so 'Study ' equals 'study'."
- `if (!name.isEmpty())` → "Skip blank tags, e.g. from 'study,,health'."
- `tags == null` → "GROUP_CONCAT returns NULL for an entry without tags."
- `habit.setStreak(streak(habit.getId()))` → "Calculate and store the streak in the object."
- `int rows = ps.executeUpdate(); if (rows == 0)` → "No row deleted means wrong id or not the user's own; we raise our own exception."
- `String bar = ""; for ... bar = bar + "#"` → "Builds #### with a loop, one # per mood point."
- `System.out.printf("%-20s %2d times   mood %.2f%n", ...)` → "Formatted printing: `%-20s` text padded to 20, `%2d` integer width 2, `%.2f` 2 decimals, `%n` new line."
- `con.close()` in Main → "Closes the connection when the user leaves."
- `public class Main` / `private static UserManager users;` → "Static fields shared by all menu methods; created once in `main`."
- `catch (SQLException e)` in `loginScreen` → "The only likely database error on register is a duplicate email, so we say that and show the real message."

### I. Tricky questions and how to respond

- **"What is `Statement.RETURN_GENERATED_KEYS`?"** → "A flag telling JDBC to remember the auto-generated id so we can read it." (If he goes deeper: "I know how we use it; the internals are the driver's job.")
- **"What is the JVM / JRE / JDK?"** → JDK = tools to develop (javac). JRE = to run. JVM = the virtual machine that runs bytecode. `javac` makes `.class` files (bytecode), `java` runs them on the JVM.
- **"What does `javac -cp "lib/*" -d out src/*.java` mean?"** → Compile all files in `src`, with the jars in `lib` on the classpath, put the `.class` files in `out`.
- **"What is a generic (`ArrayList<Habit>`)?"** → The angle brackets say what type the list holds, so the compiler checks we only add Habits.
- **"What is the difference between `String` and `StringBuilder`?"** → Strings never change; `bar = bar + "#"` creates a new String each time. For long loops StringBuilder is better; for 5 characters it's fine.
- **Out of syllabus (Spring, REST, Docker, ORM...)** → "We deliberately avoided frameworks; this project only uses plain Java and JDBC." If asked about the web version: "That's a separate earlier version; the Java part is this console app."
- **When you truly don't know:** "I'm not sure about that detail, but here is how I'd find out / what I do know about it." Never invent an answer.

---

## 12. Honest limitations

Say these yourself before he asks; it shows you understand the trade-offs.

1. **Passwords:** SHA-256 without salt. Real systems use bcrypt/argon2 with a salt.
2. **DB password is in `Db.java`** – fine locally; should be an environment variable.
3. **Resources:** statements are closed manually; if an exception happens in the middle, they are only released when the program ends. `try/finally` (or try-with-resources) is the improvement.
4. **No transactions:** "add entry + its tags" is several statements; if one failed midway, we could have an entry without all tags.
5. **Streak queries:** one query per day checked – simple, not the fastest.
6. **Console only:** no GUI/web; single user at a time.
7. **No edit/update of entries** (only add/delete) – kept the menu short.
8. **Single shared connection** (no pool).

---

## 13. Splitting the explanation between teammates

Each person should know their part completely *and* the one-page overview (sections 1–2).

| Person | Files | What they should be able to explain |
|---|---|---|
| **A – Foundation** | `Db`, `Input`, `Main`, `schema.sql` (tables part) | Connection, URL, menu flow, `switch`, buffered input, the table design / ER diagram |
| **B – Users + Check-ins** | `User`, `CheckIn`, `UserManager`, `CheckInManager`, `sample_checkins.csv` | Login and hashing, the upsert, UNIQUE per day, CSV import with `BufferedReader` |
| **C – Habits** | `Habit`, `HabitManager` | habit_logs idea, tick/untick, streak algorithm, `AppException` use |
| **D – Journal + Tags + Report** | `JournalEntry`, `Tag`, `JournalManager`, `TagManager`, `ReportManager` | Many-to-many, JOINs, GROUP BY, LIKE, export with `BufferedWriter` |
| **Everyone** | `Showable`, `Entity`, `AppException` | Inheritance, abstract class, interface, polymorphism, custom exception |

**Practice drill:** sit in a group; one person opens a random file and points at a random line; another explains it. Rotate. Do this 20 times.

---

## 14. Running it (short version)

1. MySQL running. Create the database and data (this also resets it any time):
   `mysql -u root -p < schema.sql`
2. Open `src/Db.java` and set `PASSWORD` to your MySQL root password.
3. In the `backend_java` folder: `run.bat` (compiles and runs). Or manually:
   ```
   javac -cp "lib/*" -d out src/*.java
   java -cp "out;lib/*" Main
   ```
   (On Mac/Linux use `:` instead of `;` in the classpath.)
4. Log in: `demo@sankalp.app` / `demo1234`.

**Common errors**

| Message | Meaning / fix |
|---|---|
| `Access denied for user 'root'` | Wrong `PASSWORD` in `Db.java` |
| `Unknown database 'sankalp_java'` | You haven't run `schema.sql` yet |
| `Communications link failure` | MySQL is not running (start the MySQL service) |
| `No suitable driver` / `ClassNotFoundException` | Missing `lib/*` in the classpath – use `run.bat` |
| `javac is not recognized` | JDK is not on PATH – use IntelliJ's terminal or add the JDK `bin` folder |
| `Could not find or load main class Main` | Run the `java` command from inside `backend_java`, after compiling |
| Wrong login for demo user | You re-created the DB without the demo data – run `schema.sql` again |
