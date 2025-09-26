import os
from entra_connection import AsyncEntraConnection
from psycopg_pool import AsyncConnectionPool
import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
hostname = os.getenv("HOSTNAME")
database = os.getenv("DATABASE")

# IMPORTANT! This code is for demonstration purposes only. It's not suitable for use in production.
# For example, tokens issued by Microsoft Entra ID have a limited lifetime (24 hours by default).
# In production code, you need to implement a token refresh policy.

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def get_connection_uri():
    # Read URI parameters from the environment
    async with AsyncConnectionPool(
        min_size=1, max_size=2,
        connection_class=AsyncEntraConnection,
        kwargs=dict(
            host=hostname,            
            dbname=database,
            sslmode="require",
           
        ),
    ) as pool:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT version();")
                print(await cur.fetchone())

async def main():
    await get_connection_uri()

if __name__ == "__main__":
    asyncio.run(main())
