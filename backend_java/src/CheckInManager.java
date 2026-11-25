import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

// Everything about the checkins table.
public class CheckInManager {

    private Connection con;

    public CheckInManager(Connection con) {
        this.con = con;
    }

    // Save today's check-in. If there already is one for today, UPDATE it instead
    // (the UNIQUE(user_id, checkin_date) rule in the table is what triggers ON DUPLICATE KEY).
    public void saveToday(int userId, int mood, int energy, String note) throws SQLException, AppException {
        if (mood < 1 || mood > 5 || energy < 1 || energy > 5) {
            throw new AppException("Mood and energy must be between 1 and 5.");
        }
        String sql = "INSERT INTO checkins (user_id, checkin_date, mood, energy, note) VALUES (?, CURDATE(), ?, ?, ?) "
                + "ON DUPLICATE KEY UPDATE mood = ?, energy = ?, note = ?";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setInt(1, userId);
        ps.setInt(2, mood);
        ps.setInt(3, energy);
        ps.setString(4, note);
        ps.setInt(5, mood);
        ps.setInt(6, energy);
        ps.setString(7, note);
        ps.executeUpdate();
        ps.close();
    }

    // Check-ins of the last N days, newest first.
    public ArrayList<CheckIn> lastDays(int userId, int days) throws SQLException {
        String sql = "SELECT id, checkin_date, mood, energy, note FROM checkins "
                + "WHERE user_id = ? AND checkin_date >= DATE_SUB(CURDATE(), INTERVAL ? DAY) "
                + "ORDER BY checkin_date DESC";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setInt(1, userId);
        ps.setInt(2, days);
        ResultSet rs = ps.executeQuery();

        ArrayList<CheckIn> list = new ArrayList<CheckIn>();
        while (rs.next()) {
            list.add(new CheckIn(rs.getInt("id"), rs.getString("checkin_date"), rs.getInt("mood"),
                    rs.getInt("energy"), rs.getString("note")));
        }
        rs.close();
        ps.close();
        return list;
    }

    // Read a CSV text file line by line and save each line as a check-in.
    // Each line looks like:  2026-11-20,4,3,felt fine
    // Returns how many lines were saved.
    public int importCsv(int userId, String fileName) throws IOException, SQLException {
        BufferedReader reader = new BufferedReader(new FileReader(fileName)); // file -> characters -> buffer
        String sql = "INSERT INTO checkins (user_id, checkin_date, mood, energy, note) VALUES (?, ?, ?, ?, ?) "
                + "ON DUPLICATE KEY UPDATE mood = ?, energy = ?, note = ?";
        PreparedStatement ps = con.prepareStatement(sql);

        int count = 0;
        String line;
        while ((line = reader.readLine()) != null) { // readLine gives null at the end of the file
            String[] parts = line.split(",", 4);      // cut the line at commas into at most 4 pieces
            int mood = Integer.parseInt(parts[1].trim());
            int energy = Integer.parseInt(parts[2].trim());
            ps.setInt(1, userId);
            ps.setString(2, parts[0].trim());
            ps.setInt(3, mood);
            ps.setInt(4, energy);
            ps.setString(5, parts[3].trim());
            ps.setInt(6, mood);
            ps.setInt(7, energy);
            ps.setString(8, parts[3].trim());
            ps.executeUpdate();
            count++;
        }
        ps.close();
        reader.close();
        return count;
    }
}
