import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

// The "report": shows what SQL aggregate functions (COUNT, AVG) and JOINs can tell us.
public class ReportManager {

    private Connection con;

    public ReportManager(Connection con) {
        this.con = con;
    }

    public void print(int userId) throws SQLException {
        // 1) Averages over the last 30 days -- one row of aggregates, no GROUP BY needed.
        String sql1 = "SELECT COUNT(*) AS days, AVG(mood) AS avg_mood, AVG(energy) AS avg_energy FROM checkins "
                + "WHERE user_id = ? AND checkin_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)";
        PreparedStatement ps = con.prepareStatement(sql1);
        ps.setInt(1, userId);
        ResultSet rs = ps.executeQuery();
        rs.next();
        double overall = rs.getDouble("avg_mood");
        System.out.println("--- Last 30 days ---");
        System.out.printf("Check-ins: %d   Average mood: %.2f   Average energy: %.2f%n",
                rs.getInt("days"), overall, rs.getDouble("avg_energy"));
        rs.close();
        ps.close();

        // 2) Average mood on the days each habit was done.
        //    habits JOIN habit_logs  -> the days the habit was done
        //    JOIN checkins           -> the mood on exactly that day
        String sql2 = "SELECT h.name, COUNT(*) AS times, AVG(c.mood) AS avg_mood "
                + "FROM habits h "
                + "JOIN habit_logs l ON l.habit_id = h.id "
                + "JOIN checkins c ON c.user_id = h.user_id AND c.checkin_date = l.done_date "
                + "WHERE h.user_id = ? GROUP BY h.id, h.name ORDER BY avg_mood DESC";
        ps = con.prepareStatement(sql2);
        ps.setInt(1, userId);
        rs = ps.executeQuery();
        System.out.println();
        System.out.println("--- Average mood on days you did each habit (overall average: "
                + String.format("%.2f", overall) + ") ---");
        while (rs.next()) {
            System.out.printf("%-20s %2d times   mood %.2f%n", rs.getString("name"), rs.getInt("times"),
                    rs.getDouble("avg_mood"));
        }
        rs.close();
        ps.close();

        // 3) Journal entries written this month.
        String sql3 = "SELECT COUNT(*) FROM journal_entries WHERE user_id = ? "
                + "AND YEAR(created_at) = YEAR(CURDATE()) AND MONTH(created_at) = MONTH(CURDATE())";
        ps = con.prepareStatement(sql3);
        ps.setInt(1, userId);
        rs = ps.executeQuery();
        rs.next();
        System.out.println();
        System.out.println("Journal entries this month: " + rs.getInt(1));
        rs.close();
        ps.close();
    }
}
