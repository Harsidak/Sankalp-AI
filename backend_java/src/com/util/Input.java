package com.util;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class Input {
    private static BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));

    public static String text(String question) throws IOException {
        System.out.print(question);
        String line = reader.readLine();
        if (line == null) {
            return "0";
        }
        return line.trim();
    }

    // Keeps asking until the user types a whole number.
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
