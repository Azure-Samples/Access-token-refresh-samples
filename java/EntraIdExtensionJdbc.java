import java.sql.DriverManager;
import java.util.Properties;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.io.IOException;
import java.io.InputStream;
import java.io.FileInputStream;
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

public class EntraIdExtensionJdbc {
    public static void main(String[] args) {
        Properties config = loadApplicationProperties();

        // Get URL and user from properties
        String url = config.getProperty("url");
        String user = config.getProperty("user");

        if (url == null || url.trim().isEmpty()) {
            System.err.println("URL not found in application.properties");
            return;
        }

        if (user == null || user.trim().isEmpty()) {
            System.err.println("User not found in application.properties");
            return;
        }

        // Demonstrate basic JDBC connection
        demonstrateBasicJdbc(url, user);

        System.out.println("\n" + "=".repeat(60) + "\n");

        // Demonstrate connection pooling
        demonstrateConnectionPooling(url, user);
    }

    /**
     * Demonstrate basic JDBC connection using DriverManager and Azure
     * authentication plugin
     */
    private static void demonstrateBasicJdbc(String url, String user) {
        System.out.println("Basic JDBC Connection (no pooling):");

        // Create connection properties
        Properties props = new Properties();
        props.setProperty("user", user);

        try (Connection conn = DriverManager.getConnection(url, props)) {
            System.out.println("Connected successfully using automatic token retrieval!");
            var rs = conn.createStatement().executeQuery("SELECT current_user;");
            if (rs.next()) {
                System.out.println("Current database user: " + rs.getString(1));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * Demonstrate connection pooling with HikariCP using Azure authentication
     * plugin
     */
    private static void demonstrateConnectionPooling(String jdbcUrl, String user) {
        System.out.println("Connection Pooling with HikariCP:");

        // Configure HikariCP with JDBC URL (the Azure plugin handles authentication)
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(jdbcUrl);
        config.setUsername(user);

        // Pool configuration
        config.setMaximumPoolSize(10);
        config.setMinimumIdle(2);
        config.setConnectionTimeout(30000); // 30 seconds
        config.setIdleTimeout(600000); // 10 minutes
        config.setMaxLifetime(1800000); // 30 minutes (less than token lifetime)
        config.setPoolName("PostgreSQL-Azure-Pool");

        try (HikariDataSource pooledDataSource = new HikariDataSource(config)) {
            System.out.println("Connection pool created with " + config.getMaximumPoolSize() + " max connections");
            // Execute multiple queries using the pool
            for (int i = 1; i <= 3; i++) {
                try (Connection conn = pooledDataSource.getConnection();
                        Statement stmt = conn.createStatement();
                        ResultSet rs = stmt.executeQuery(
                                "SELECT 'Query #" + i + "' AS query_num, NOW() AS time, current_user AS user")) {

                    if (rs.next()) {
                        System.out.println("  " + rs.getString("query_num") + " - " + rs.getTimestamp("time")
                                + " - User: " + rs.getString("user"));
                    }

                } catch (Exception e) {
                    System.err.println("Query " + i + " failed:");
                    e.printStackTrace();
                }
            }

            System.out.println("All pooled queries completed successfully");
            System.out.println("Pool stats - Active: " + pooledDataSource.getHikariPoolMXBean().getActiveConnections()
                    + ", Idle: " + pooledDataSource.getHikariPoolMXBean().getIdleConnections() + ", Total: "
                    + pooledDataSource.getHikariPoolMXBean().getTotalConnections());

        } catch (Exception e) {
            System.err.println("Connection pooling failed:");
            e.printStackTrace();
        }
    }

    private static Properties loadApplicationProperties() {
        Properties config = new Properties();
        try (InputStream input = EntraIdExtensionJdbc.class.getClassLoader()
                .getResourceAsStream("application.properties")) {
            if (input == null) {
                System.err.println("Unable to find application.properties");
                System.exit(1);
            }
            config.load(input);
            return config;
        } catch (IOException e) {
            System.err.println("Error loading application.properties: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
            return config;
        }
    }
}
