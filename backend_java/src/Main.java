import com.util.AppException;
import java.io.IOException;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.ArrayList;
import com.dao.CheckInDao;
import com.dao.HabitDao;
import com.dao.JournalDao;
import com.dao.ReportDao;
import com.dao.TagDao;
import com.dao.UserDao;
import com.model.CheckIn;
import com.model.Habit;
import com.model.JournalEntry;
import com.model.Tag;
import com.model.User;
import com.util.Db;
import com.util.Input;

// The menu. It only asks questions and prints answers; all database work is in the dao classes.
public class Main {
    private static UserDao users;
    private static CheckInDao checkIns;
    private static HabitDao habits;
    private static JournalDao journal;
    private static TagDao tags;
    private static ReportDao report;

    public static void main(String[] args) throws Exception {
        Connection con = Db.connect();
        System.out.println("Connected to MySQL.");
        users = new UserDao(con);
        checkIns = new CheckInDao(con);
        habits = new HabitDao(con);
        journal = new JournalDao(con);
        tags = new TagDao(con);
        report = new ReportDao(con);

        System.out.println("=== SANKALP : mood & habit tracker ===");
        User user = loginScreen();
        if (user != null) {
            System.out.print("\nWelcome, ");
            user.show();
            mainMenu(user.getId());
        }
        con.close();
        System.out.println("Goodbye!");
    }

    // Asks until the user logs in (returns the User) or chooses exit (returns null).
    private static User loginScreen() throws Exception {
        while (true) {
            System.out.println("\n1. Login\n2. Register\n0. Exit");
            int choice = Input.number("Choose: ");
            try {
                if (choice == 1) {
                    String email = Input.text("Email: ");
                    String password = Input.text("Password: ");
                    User user = users.login(email, password);
                    if (user != null) {
                        return user;
                    }
                    System.out.println("Wrong email or password.");
                } else if (choice == 2) {
                    String name = Input.text("Full name: ");
                    String email = Input.text("Email: ");
                    String password = Input.text("Password: ");
                    users.register(email, password, name);
                    System.out.println("Account created. Now log in.");
                } else if (choice == 0) {
                    return null;
                }
            } catch (SQLException e) {
                if (e.getErrorCode() == 1062) { // 1062 = MySQL "duplicate entry" error
                    System.out.println("That email is already registered.");
                } else {
                    System.out.println("Database error: " + e.getMessage());
                }
            }
        }
    }

    private static void mainMenu(int userId) throws Exception {
        while (true) {
            System.out.println();
            System.out.println("--- CHECK-INS ---");
            System.out.println(" 1. Check in today");
            System.out.println(" 2. Show last 14 days");
            System.out.println(" 3. Import check-ins from a CSV file");
            System.out.println("--- HABITS ---");
            System.out.println(" 4. Show habits");
            System.out.println(" 5. Tick / untick a habit for today");
            System.out.println(" 6. Add a habit");
            System.out.println(" 7. Delete a habit");
            System.out.println("--- JOURNAL ---");
            System.out.println(" 8. Write an entry");
            System.out.println(" 9. List / search entries");
            System.out.println("10. Read an entry");
            System.out.println("11. Delete an entry");
            System.out.println("12. Export entries to a text file");
            System.out.println("--- TAGS ---");
            System.out.println("13. Show tags");
            System.out.println("14. Delete a tag");
            System.out.println("--- REPORT ---");
            System.out.println("15. Show report");
            System.out.println(" 0. Exit");
            int choice = Input.number("Choose: ");
            if (choice == 0) {
                return;
            }

            try {
                switch (choice) {
                    case 1:
                        int mood = Input.number("Mood today (1-5): ");
                        int energy = Input.number("Energy today (1-5): ");
                        String note = Input.text("Note: ");
                        checkIns.saveToday(userId, mood, energy, note);
                        System.out.println("Saved.");
                        break;
                    case 2:
                        for (CheckIn c : checkIns.lastDays(userId, 14)) {
                            c.show();
                        }
                        break;
                    case 3:
                        String csvName = Input.text("CSV file name (for example sample_checkins.csv): ");
                        int imported = checkIns.importCsv(userId, csvName);
                        System.out.println("Imported " + imported + " check-ins.");
                        break;
                    case 4:
                        for (Habit h : habits.list(userId)) {
                            h.show();
                        }
                        break;
                    case 5:
                        int habitId = Input.number("Habit number: ");
                        boolean nowDone = habits.toggleToday(userId, habitId);
                        System.out.println(nowDone ? "Ticked for today." : "Unticked.");
                        break;
                    case 6:
                        habits.add(userId, Input.text("Habit name: "));
                        System.out.println("Habit added.");
                        break;
                    case 7:
                        habits.delete(userId, Input.number("Habit number: "));
                        System.out.println("Habit deleted.");
                        break;
                    case 8:
                        String title = Input.text("Title: ");
                        String content = Input.text("Write your entry: ");
                        String tagText = Input.text("Tags separated by commas (or leave empty): ");
                        journal.add(userId, title, content, tagText);
                        System.out.println("Entry saved.");
                        break;
                    case 9:
                        String search = Input.text("Search word (leave empty for all): ");
                        ArrayList<JournalEntry> found = journal.list(userId, search);
                        for (JournalEntry e : found) {
                            e.show();
                        }
                        System.out.println(found.size() + " entries.");
                        break;
                    case 10:
                        journal.get(userId, Input.number("Entry number: ")).showFull();
                        break;
                    case 11:
                        journal.delete(userId, Input.number("Entry number: "));
                        System.out.println("Entry deleted.");
                        break;
                    case 12:
                        int written = journal.exportToFile(userId, "journal_export.txt");
                        System.out.println("Wrote " + written + " entries to journal_export.txt");
                        break;
                    case 13:
                        for (Tag t : tags.listWithCounts(userId)) {
                            t.show();
                        }
                        break;
                    case 14:
                        tags.delete(userId, Input.number("Tag number: "));
                        System.out.println("Tag deleted.");
                        break;
                    case 15:
                        report.print(userId);
                        break;
                    default:
                        System.out.println("Please choose a number from the menu.");
                }
            } catch (AppException e) {
                System.out.println("Problem: " + e.getMessage());
            } catch (SQLException e) {
                System.out.println("Database error: " + e.getMessage());
            } catch (IOException e) {
                System.out.println("File error: " + e.getMessage());
            }
        }
    }
}
