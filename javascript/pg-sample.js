import pg from "pg";
import { getEntraTokenPassword } from './entra-connection.js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Load .env file from the same directory as this script
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, '.env') });

const { Pool } = pg;

const pool = new Pool({
  host: process.env.PGHOST,
  port: Number(process.env.PGPORT || 5432),
  database: process.env.PGDATABASE,
  user: process.env.PGUSER,            
  password: getEntraTokenPassword,      
  ssl: {
    rejectUnauthorized: false // or true with proper certificates
  },         
  connectionTimeoutMillis: 20000,
  idleTimeoutMillis: 30000,
});

async function main() {
  try {
    console.log('Testing multiple connections from the pool...\n');

    // Function to simulate a database operation
    async function performQuery(connectionNumber) {
      const client = await pool.connect();
      try {
        console.log(`Connection ${connectionNumber}: Acquired from pool`);
        
        const { rows } = await client.query(`
          SELECT 
            current_user, 
            now() as server_time,
            pg_backend_pid() as backend_pid,
            '${connectionNumber}' as connection_number
        `);
        
        console.log(`Connection ${connectionNumber} result:`, rows[0]);
        
        // Simulate some work with a small delay
        await new Promise(resolve => setTimeout(resolve, 100));
        
        return rows[0];
      } finally {
        console.log(`Connection ${connectionNumber}: Released back to pool`);
        client.release();
      }
    }

    // Test getting multiple connections simultaneously
    const connectionPromises = [];
    for (let i = 1; i <= 5; i++) {
      connectionPromises.push(performQuery(i));
    }

    const results = await Promise.all(connectionPromises);
    
    console.log('\n=== Summary ===');
    console.log('All connections completed successfully!');
    console.log('Backend PIDs used:', results.map(r => r.backend_pid));
    
    // Check if different backend PIDs were used (indicating different physical connections)
    const uniquePids = new Set(results.map(r => r.backend_pid));
    console.log(`Used ${uniquePids.size} unique database connections out of ${results.length} requests`);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    try {
      await pool.end();
      console.log('\nPool closed.');
    } catch (closeError) {
      console.error('⚠️  Error closing pool:', closeError.message);
    }
  }
}

// Run the main function and handle any unhandled errors
main().catch((error) => {
  console.error('💥 Unhandled error in main function:', error);
  process.exit(1);
});

