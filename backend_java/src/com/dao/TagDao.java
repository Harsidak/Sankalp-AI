package com.dao;

import com.util.AppException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import com.model.Tag;

// Everything about the tags table.
public class TagDao {
    private Connection con;

    public TagDao(Connection con) {
        this.con = con;
    }

    // LEFT JOIN keeps tags used by zero entries (a normal JOIN would drop them).
    public ArrayList<Tag> listWithCounts(int userId) throws SQLException {
        String sql = "SELECT t.id, t.name, COUNT(jt.journal_id) AS entry_count "
                + "FROM tags t LEFT JOIN journal_tags jt ON jt.tag_id = t.id "
                + "WHERE t.user_id = ? GROUP BY t.id, t.name ORDER BY t.name";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setInt(1, userId);
        ResultSet rs = ps.executeQuery();
        ArrayList<Tag> list = new ArrayList<Tag>();
        while (rs.next()) {
            list.add(new Tag(rs.getInt("id"), rs.getString("name"), rs.getInt("entry_count")));
        }
        rs.close();
        ps.close();
        return list;
    }

    // The tag leaves the entries (journal_tags rows go by ON DELETE CASCADE); the entries stay.
    public void delete(int userId, int tagId) throws SQLException, AppException {
        PreparedStatement ps = con.prepareStatement("DELETE FROM tags WHERE id = ? AND user_id = ?");
        ps.setInt(1, tagId);
        ps.setInt(2, userId);
        int rows = ps.executeUpdate();
        ps.close();
        if (rows == 0) {
            throw new AppException("You have no tag with that number.");
        }
    }
}
