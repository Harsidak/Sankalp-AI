import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;

// Everything about journal_entries (and the entry_tags join table).
public class JournalManager {

    private Connection con;

    public JournalManager(Connection con) {
        this.con = con;
    }

    // Save an entry, then attach its tags. tagsText looks like "study, health" (can be empty).
    public void add(int userId, String title, String content, String tagsText) throws SQLException {
        String sql = "INSERT INTO journal_entries (user_id, title, content) VALUES (?, ?, ?)";
        // RETURN_GENERATED_KEYS lets us ask MySQL "which id did you just give this row?"
        PreparedStatement ps = con.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
        ps.setInt(1, userId);
        ps.setString(2, title);
        ps.setString(3, content);
        ps.executeUpdate();
        ResultSet keys = ps.getGeneratedKeys();
        keys.next();
        int entryId = keys.getInt(1);
        keys.close();
        ps.close();

        String[] names = tagsText.split(","); // "study, health" -> ["study", " health"]
        for (String name : names) {
            name = name.trim().toLowerCase();
            if (!name.isEmpty()) {
                attachTag(userId, entryId, name);
            }
        }
    }

    // Make sure the tag exists, then link it to the entry in the join table.
    // INSERT IGNORE = "if this would break a UNIQUE / PRIMARY KEY rule, silently skip it".
    private void attachTag(int userId, int entryId, String tagName) throws SQLException {
        PreparedStatement insertTag = con.prepareStatement("INSERT IGNORE INTO tags (user_id, name) VALUES (?, ?)");
        insertTag.setInt(1, userId);
        insertTag.setString(2, tagName);
        insertTag.executeUpdate();
        insertTag.close();

        PreparedStatement findTag = con.prepareStatement("SELECT id FROM tags WHERE user_id = ? AND name = ?");
        findTag.setInt(1, userId);
        findTag.setString(2, tagName);
        ResultSet rs = findTag.executeQuery();
        rs.next();
        int tagId = rs.getInt("id");
        rs.close();
        findTag.close();

        PreparedStatement link = con.prepareStatement("INSERT IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?, ?)");
        link.setInt(1, entryId);
        link.setInt(2, tagId);
        link.executeUpdate();
        link.close();
    }

    // List entries, newest first. If search is not empty, only entries whose title or content contains it.
    // Two LEFT JOINs go entry -> entry_tags -> tags; GROUP_CONCAT glues the tag names of one entry into one text.
    public ArrayList<JournalEntry> list(int userId, String search) throws SQLException {
        String sql = "SELECT e.id, e.title, e.content, e.created_at, GROUP_CONCAT(t.name SEPARATOR ', ') AS tags "
                + "FROM journal_entries e "
                + "LEFT JOIN entry_tags et ON et.entry_id = e.id "
                + "LEFT JOIN tags t ON t.id = et.tag_id "
                + "WHERE e.user_id = ? AND (e.title LIKE ? OR e.content LIKE ?) "
                + "GROUP BY e.id ORDER BY e.created_at DESC";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setInt(1, userId);
        ps.setString(2, "%" + search + "%"); // % means "anything", so %walk% matches "a walk today"
        ps.setString(3, "%" + search + "%");
        ResultSet rs = ps.executeQuery();

        ArrayList<JournalEntry> list = new ArrayList<JournalEntry>();
        while (rs.next()) {
            String tags = rs.getString("tags");
            if (tags == null) { // an entry without tags gives NULL
                tags = "";
            }
            list.add(new JournalEntry(rs.getInt("id"), rs.getString("title"), rs.getString("content"),
                    rs.getString("created_at"), tags));
        }
        rs.close();
        ps.close();
        return list;
    }

    // Find one entry in the list by its id.
    public JournalEntry get(int userId, int entryId) throws SQLException, AppException {
        for (JournalEntry entry : list(userId, "")) {
            if (entry.getId() == entryId) {
                return entry;
            }
        }
        throw new AppException("You have no entry with that number.");
    }

    public void delete(int userId, int entryId) throws SQLException, AppException {
        PreparedStatement ps = con.prepareStatement("DELETE FROM journal_entries WHERE id = ? AND user_id = ?");
        ps.setInt(1, entryId);
        ps.setInt(2, userId);
        int rows = ps.executeUpdate();
        ps.close();
        if (rows == 0) {
            throw new AppException("You have no entry with that number.");
        }
    }

    // Write all entries into a text file. Returns how many were written.
    public int exportToFile(int userId, String fileName) throws SQLException, IOException {
        ArrayList<JournalEntry> entries = list(userId, "");

        // characters -> buffer -> file. The buffer collects text and writes it in bigger chunks (faster).
        BufferedWriter writer = new BufferedWriter(new FileWriter(fileName));
        for (JournalEntry entry : entries) {
            writer.write(entry.getCreatedAt() + "  " + entry.getTitle() + "  [" + entry.getTags() + "]");
            writer.newLine();
            writer.write(entry.getContent());
            writer.newLine();
            writer.newLine();
        }
        writer.close(); // close() also flushes what is still in the buffer into the file
        return entries.size();
    }
}
