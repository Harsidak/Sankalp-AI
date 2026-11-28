package com.util;

import com.mysql.cj.jdbc.MysqlDataSource;
import java.sql.Connection;
import java.sql.SQLException;

// The only place that knows how to reach MySQL (MySQL Connector's MysqlDataSource). Put your own MySQL password in PASSWORD.
public class Db {
    private static final String PASSWORD = "your_pass";

    public static Connection connect() throws SQLException {
        MysqlDataSource ds = new MysqlDataSource();
        ds.setServerName("localhost");
        ds.setPortNumber(3306);
        ds.setDatabaseName("sankalp_java");
        ds.setUser("root");
        ds.setPassword(PASSWORD);
        return ds.getConnection();
    }
}
