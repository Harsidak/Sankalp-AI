package com.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import com.model.User;

public class UserDao {
    private Connection con;

    public UserDao(Connection con) {
        this.con = con;
    }

    public void register(String email, String password, String fullName) throws SQLException {
        String sql = "INSERT INTO users (email, password_hash, full_name) VALUES (?, SHA2(?, 256), ?)";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setString(1, email);
        ps.setString(2, password);
        ps.setString(3, fullName);
        ps.executeUpdate(); // executeUpdate = INSERT / UPDATE / DELETE
        ps.close();
    }

    public User login(String email, String password) throws SQLException {
        String sql = "SELECT id, email, full_name FROM users WHERE email = ? AND password_hash = SHA2(?, 256)";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setString(1, email);
        ps.setString(2, password);
        ResultSet rs = ps.executeQuery(); // executeQuery = SELECT
        User user = null;
        if (rs.next()) { // moves to the next row, false when there is none
            user = new User(rs.getInt("id"), rs.getString("email"), rs.getString("full_name"));
        }
        rs.close();
        ps.close();
        return user;
    }
}
