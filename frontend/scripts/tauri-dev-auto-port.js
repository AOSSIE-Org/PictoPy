const net = require('net');
const { spawn } = require('child_process');

// Range of ports to check (Vite's default + alternatives)
const PORT_RANGE_START = 5173;
const PORT_RANGE_END = 5182;

/**
 * Check if a port is available
 * @param {number} port - Port to check
 * @returns {Promise<boolean>} - True if port is available
 */
function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();

    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(false);
      } else {
        console.warn(`Unexpected error checking port ${port}:`, err.message);
        resolve(false);
      }
    });

    server.once('listening', () => {
      server.close();
      resolve(true);
    });

    server.listen(port, 'localhost');
  });
}

/**
 * Find the first available port in range
 * @returns {Promise<number|null>} - Available port or null
 */
async function findAvailablePort() {
  for (let port = PORT_RANGE_START; port <= PORT_RANGE_END; port++) {
    if (await isPortAvailable(port)) {
      return port;
    }
  }
  return null;
}

/**
 * Main function
 */
async function main() {
  console.log('\n🔍 Detecting available port for Tauri development...');

  const port = await findAvailablePort();

  if (!port) {
    console.error(
      `\n❌ No available ports found in range ${PORT_RANGE_START}-${PORT_RANGE_END}`,
    );
    console.error(
      'Please free up a port or manually configure the port in tauri.conf.json',
    );
    process.exit(1);
  }

  console.log(`✅ Found available port: ${port}`);
  console.log('🚀 Starting Tauri dev server...\n');

  // Start Tauri dev with CLI flags (no config file modification)
  const tauri = spawn(
    'npm',
    [
      'run',
      'tauri',
      'dev',
      '--',
      '--dev-url',
      `http://localhost:${port}`,
      '--port',
      port.toString(),
    ],
    {
      stdio: 'inherit',
      shell: true,
      env: {
        ...process.env,
        VITE_PORT: port.toString(),
        TAURI_CLI_PORT: port.toString(),
        TAURI_DEV_HOST: 'localhost',
      },
    },
  );

  tauri.on('error', (error) => {
    console.error('Failed to start Tauri dev server:', error);
    process.exit(1);
  });

  tauri.on('exit', (code) => {
    process.exit(code || 0);
  });
}

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
