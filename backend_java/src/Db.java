import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

// The only place that knows HOW to reach MySQL.
// Change PASSWORD to your own MySQL root password.
public class Db {

    // jdbc:mysql://  host : port / database name
    private static final String URL = "jdbc:mysql://localhost:3306/sankalp_java?useSSL=false&allowPublicKeyRetrieval=true";
    private static final String USER = "root";
    private static final String PASSWORD = "your_password";

    // Opens a connection. Every manager class receives this one connection.
    public static Connection connect() throws SQLException {
        return DriverManager.getConnection(URL, USER, PASSWORD);
    }
}
