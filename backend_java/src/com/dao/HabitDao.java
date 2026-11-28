package com.dao;

import com.util.AppException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import com.model.Habit;

// Everything about the habits and habit_logs tables.
public class HabitDao {
    private Connection con;

    public HabitDao(Connection con) {
        this.con = con;
    }

    public void add(int userId, String name) throws SQLException {
        PreparedStatement ps = con.prepareStatement("INSERT INTO habits (user_id, name) VALUES (?, ?)");
        ps.setInt(1, userId);
        ps.setString(2, name);
        ps.executeUpdate();
        ps.close();
    }

    public void delete(int userId, int habitId) throws SQLException, AppException {
        PreparedStatement ps = con.prepareStatement("DELETE FROM habits WHERE id = ? AND user_id = ?");
        ps.setInt(1, habitId);
        ps.setInt(2, userId);
        int rows = ps.executeUpdate(); // number of rows changed
        ps.close();
        if (rows == 0) {
            throw new AppException("You have no habit with that number.");
        }
    }

    public ArrayList<Habit> list(int userId) throws SQLException {
        PreparedStatement ps = con.prepareStatement("SELECT id, name FROM habits WHERE user_id = ? ORDER BY id");
        ps.setInt(1, userId);
        ResultSet rs = ps.executeQuery();
        ArrayList<Habit> list = new ArrayList<Habit>();
        while (rs.next()) {
            list.add(new Habit(rs.getInt("id"), rs.getString("name")));
        }
        rs.close();
        ps.close();
        for (Habit habit : list) {
            habit.setDoneToday(isDone(habit.getId(), 0));
            habit.setStreak(streak(habit.getId()));
        }
        return list;
    }

    public boolean toggleToday(int userId, int habitId) throws SQLException, AppException {
        PreparedStatement check = con.prepareStatement("SELECT COUNT(*) FROM habits WHERE id = ? AND user_id = ?");
        check.setInt(1, habitId);
        check.setInt(2, userId);
        ResultSet rs = check.executeQuery();
        rs.next();
        int found = rs.getInt(1);
        rs.close();
        check.close();
        if (found == 0) {
            throw new AppException("You have no habit with that number.");
        }

        String sql;
        boolean nowDone;
        if (isDone(habitId, 0)) {
            sql = "DELETE FROM habit_logs WHERE habit_id = ? AND done_date = CURDATE()";
            nowDone = false;
        } else {
            sql = "INSERT INTO habit_logs (habit_id, done_date) VALUES (?, CURDATE())";
            nowDone = true;
        }
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setInt(1, habitId);
        ps.executeUpdate();
        ps.close();
        return nowDone;
    }

    private boolean isDone(int habitId, int daysAgo) throws SQLException {
        String sql = "SELECT COUNT(*) FROM habit_logs WHERE habit_id = ? AND done_date = DATE_SUB(CURDATE(), INTERVAL ? DAY)";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setInt(1, habitId);
        ps.setInt(2, daysAgo);
        ResultSet rs = ps.executeQuery();
        rs.next();
        boolean done = rs.getInt(1) > 0;
        rs.close();
        ps.close();
        return done;
    }

    private int streak(int habitId) throws SQLException {
        int start = 0;
        if (!isDone(habitId, 0)) {
            start = 1;
        }
        int count = 0;
        while (isDone(habitId, start + count)) {
            count++;
        }
        return count;
    }
}
