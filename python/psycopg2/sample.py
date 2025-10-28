"""
Sample demonstrating psycopg2 connection with synchronous Entra ID authentication for Azure PostgreSQL.
"""

import os

from dotenv import load_dotenv
from psycopg2 import pool
from entra_connection import EntraConnection

# Load environment variables from .env file
load_dotenv()
hostname = os.getenv("HOSTNAME")
database = os.getenv("DATABASE", "postgres")

def main() -> None:
    # We use the EntraConnection class to enable synchronous Entra-based authentication for database access.
    # This class is applied whenever the connection pool creates a new connection, ensuring that Entra
    # authentication tokens are properly managed and refreshed so that each connection uses a valid token.
    #
    # For more details, see: https://www.psycopg.org/docs/advanced.html#subclassing-connection
    connection_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=5,
        host=hostname,
        database=database,
        connection_factory=EntraConnection,
    )

    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT now()")
            result = cur.fetchone()
            print(f"Database time: {result[0]}")
    finally:
        connection_pool.putconn(conn)
        connection_pool.closeall()


if __name__ == "__main__":
    main()
