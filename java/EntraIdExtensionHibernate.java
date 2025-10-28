import org.hibernate.Session;
import org.hibernate.SessionFactory;
import org.hibernate.cfg.Configuration;
import org.hibernate.cfg.Environment;
import java.util.Properties;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;

public class EntraIdExtensionHibernate {

    private static SessionFactory sessionFactory;

    public static void main(String[] args) {
        try {
            // Create SessionFactory
            sessionFactory = createSessionFactory();

            // Test the connection
            testDatabaseConnection();

        } catch (Exception e) {
            System.err.println("Failed to create SessionFactory or connect to database:");
            e.printStackTrace();
        } finally {
            // Clean up
            if (sessionFactory != null) {
                sessionFactory.close();
            }
        }
    }

    /**
     * Create Hibernate SessionFactory with Azure AD authentication
     */
    private static SessionFactory createSessionFactory() {
        // Load configuration from application.properties
        Properties appProps = loadApplicationProperties();

        String url = appProps.getProperty("url");
        String user = appProps.getProperty("user");

        if (url == null || url.trim().isEmpty()) {
            throw new RuntimeException("URL not found in application.properties");
        }

        if (user == null || user.trim().isEmpty()) {
            throw new RuntimeException("User not found in application.properties");
        }

        // Configure Hibernate properties
        Properties hibernateProps = new Properties();

        // Database connection settings
        hibernateProps.setProperty("hibernate.connection.driver_class", "org.postgresql.Driver");
        hibernateProps.setProperty("hibernate.connection.url", url);
        hibernateProps.setProperty("hibernate.connection.username", user);

        // Hibernate settings
        hibernateProps.setProperty(Environment.DIALECT, "org.hibernate.dialect.PostgreSQLDialect");
        hibernateProps.setProperty(Environment.SHOW_SQL, "true");
        hibernateProps.setProperty(Environment.FORMAT_SQL, "true");
        hibernateProps.setProperty(Environment.HBM2DDL_AUTO, "none"); // Don't auto-create tables

        // Connection pool settings (using Hibernate's built-in pool)
        hibernateProps.setProperty(Environment.POOL_SIZE, "5");
        hibernateProps.setProperty(Environment.AUTOCOMMIT, "true");

        try {
            Configuration configuration = new Configuration();
            configuration.setProperties(hibernateProps);

            System.out.println("Creating Hibernate SessionFactory...");
            return configuration.buildSessionFactory();

        } catch (Exception e) {
            throw new RuntimeException("Failed to create SessionFactory", e);
        }
    }

    /**
     * Load properties from application.properties file
     */
    private static Properties loadApplicationProperties() {
        Properties props = new Properties();
        try (InputStream input = new FileInputStream("application.properties")) {
            if (input == null) {
                throw new RuntimeException("Unable to find application.properties");
            }
            props.load(input);
            return props;
        } catch (IOException e) {
            throw new RuntimeException("Error loading application.properties: " + e.getMessage(), e);
        }
    }

    /**
     * Test the database connection by executing a simple query
     */
    private static void testDatabaseConnection() {
        System.out.println("Testing database connection...");

        try (Session session = sessionFactory.openSession()) {
            // Execute a simple query to test the connection
            String currentUser = session.createNativeQuery("SELECT current_user", String.class).getSingleResult();
            String currentTime = session.createNativeQuery("SELECT NOW()", String.class).getSingleResult();
            String version = session.createNativeQuery("SELECT version()", String.class).getSingleResult();

            System.out.println("Successfully connected to PostgreSQL!");
            System.out.println("Current user: " + currentUser);
            System.out.println("Current time: " + currentTime);
            System.out.println("PostgreSQL version: " + version.substring(0, Math.min(version.length(), 50)) + "...");

            // Test multiple sessions to verify connection pooling
            System.out.println("\nTesting connection pooling...");
            for (int i = 1; i <= 3; i++) {
                try (Session testSession = sessionFactory.openSession()) {
                    String result = testSession.createNativeQuery("SELECT 'Test query #" + i + "'", String.class)
                            .getSingleResult();
                    System.out.println("  " + result + " - Session created successfully");
                }
            }
            System.out.println("Connection pooling is working!");

        } catch (Exception e) {
            System.err.println("Database connection test failed:");
            e.printStackTrace();
        }
    }
}
