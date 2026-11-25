import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

// Register and log in. All SQL about the users table is here.
public class UserManager {

    private Connection con;

    public UserManager(Connection con) {
        this.con = con;
    }

    // The password is never stored as typed. MySQL's SHA2(..., 256) scrambles it into 64 characters.
    public void register(String email, String password, String fullName) throws SQLException {
        String sql = "INSERT INTO users (email, password_hash, full_name) VALUES (?, SHA2(?, 256), ?)";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setString(1, email);
        ps.setString(2, password);
        ps.setString(3, fullName);
        ps.executeUpdate(); // executeUpdate = for INSERT / UPDATE / DELETE
        ps.close();
    }

    // Returns the User if email and password match, otherwise null.
    public User login(String email, String password) throws SQLException {
        String sql = "SELECT id, email, full_name FROM users WHERE email = ? AND password_hash = SHA2(?, 256)";
        PreparedStatement ps = con.prepareStatement(sql);
        ps.setString(1, email);
        ps.setString(2, password);
        ResultSet rs = ps.executeQuery(); // executeQuery = for SELECT

        User user = null;
        if (rs.next()) { // rs.next() moves to the next row; false when there is none
            user = new User(rs.getInt("id"), rs.getString("email"), rs.getString("full_name"));
        }
        rs.close();
        ps.close();
        return user;
    }
}
