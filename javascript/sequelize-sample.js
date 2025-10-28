import dotenv from 'dotenv';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { Sequelize } from 'sequelize';
import { configureEntraIdAuth } from './entra-connection.js';

// Load .env from the same directory as this script
dotenv.config({ path: join(dirname(fileURLToPath(import.meta.url)), '.env') });

async function main() {
  let sequelize;
  
  try {
    sequelize = new Sequelize({
        dialect: 'postgres',
        host: process.env.PGHOST,
        port: Number(process.env.PGPORT || 5432),
        database: process.env.PGDATABASE,
        dialectOptions: { ssl: { rejectUnauthorized: true } },
        pool: { min: 4, max: 10, idle: 30_000 }
    });
    
    // Configure Entra ID authentication
    configureEntraIdAuth(sequelize);
    
    await sequelize.authenticate();   // triggers beforeConnect and opens a connection
    console.log('✅ Sequelize connection established successfully with Entra ID!');

    console.log('🔄 Testing concurrent queries (automatic pooling)...\n');

    async function runConcurrentQuery(queryId) {
        const startTime = Date.now();
        console.log(`Query ${queryId}: Starting...`);
        
        const [results] = await sequelize.query(`
            SELECT 
                ${queryId} as query_id,
                pg_backend_pid() as backend_pid,
                current_user,
                now() as query_time,
                pg_sleep(2) -- Simulate slow query
        `);
        
        const duration = Date.now() - startTime;
        console.log(`Query ${queryId}: Completed in ${duration}ms - Backend PID: ${results[0].backend_pid}`);
        return results[0];
    }

    const concurrentResults = await Promise.all([
        runConcurrentQuery(1),
        runConcurrentQuery(2),
        runConcurrentQuery(3),
        runConcurrentQuery(4),
        runConcurrentQuery(5)
    ]);

    // Analyze connection reuse
    const uniquePids = new Set(concurrentResults.map(r => r.backend_pid));
    console.log(`\n📊 Concurrent Query Results:`);
    console.log(`   Total queries: ${concurrentResults.length}`);
    console.log(`   Unique connections used: ${uniquePids.size}`);
    console.log(`   Connection reuse: ${uniquePids.size < concurrentResults.length ? 'YES' : 'NO'}`);

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    if (sequelize) {
      try {
        await sequelize.close();
        console.log('\n🔌 All database connections closed. Program exiting...');
      } catch (closeError) {
        console.error('⚠️  Error closing connections:', closeError.message);
      }
    }
  }
}

// Run the main function and handle any unhandled errors
main().catch((error) => {
  console.error('💥 Unhandled error in main function:', error);
  process.exit(1);
});
