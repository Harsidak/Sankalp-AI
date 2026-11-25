import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

// Reads what the user types in the terminal.
// System.in         -> raw bytes from the keyboard
// InputStreamReader -> turns bytes into characters
// BufferedReader    -> collects characters in a buffer so we can read a whole line at once
public class Input {

    private static BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));

    // Show a question, return the line the user typed (spaces at both ends removed).
    public static String text(String question) throws IOException {
        System.out.print(question);
        return reader.readLine().trim();
    }

    // Same, but keeps asking until the user types a whole number.
    public static int number(String question) throws IOException {
        while (true) {
            String line = text(question);
            try {
                return Integer.parseInt(line);
            } catch (NumberFormatException e) {
                System.out.println("Please type a number.");
            }
        }
    }
}
