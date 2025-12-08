const net = require('net');
const fs = require('fs');
const path = require('path');

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
        resolve(false);
      }
    });
    
    server.once('listening', () => {
      server.close();
      resolve(true);
    });
    
    server.listen(port);
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
 * Update tauri.conf.json with the selected port
 * @param {number} port - Port to use
 */
function updateTauriConfig(port) {
  const configPath = path.join(__dirname, '..', 'src-tauri', 'tauri.conf.json');
  
  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    
    // Update devUrl and beforeDevCommand
    config.build.devUrl = `http://localhost:${port}`;
    config.build.beforeDevCommand = `npm run dev -- --port ${port}`;
    
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    console.log(`✓ Updated Tauri config to use port ${port}`);
  } catch (error) {
    console.error('Error updating Tauri config:', error);
    process.exit(1);
  }
}

/**
 * Main function
 */
async function main() {
  console.log('\nDetecting available port for Tauri development...');
  
  const port = await findAvailablePort();
  
  if (!port) {
    console.error(`\n✗ No available ports found in range ${PORT_RANGE_START}-${PORT_RANGE_END}`);
    console.error('Please free up a port or manually configure the port in tauri.conf.json');
    process.exit(1);
  }
  
  console.log(`Found available port: ${port}`);
  updateTauriConfig(port);
  
  // Set environment variables
  process.env.VITE_PORT = port.toString();
  process.env.TAURI_MODE = 'development';
  
  console.log('Starting Tauri dev server...\n');
  
  // Start Tauri dev
  const { spawn } = require('child_process');
  const tauri = spawn('npm', ['run', 'tauri', 'dev'], {
    stdio: 'inherit',
    shell: true,
    env: { ...process.env, VITE_PORT: port.toString() }
  });
  
  tauri.on('exit', (code) => {
    process.exit(code);
  });
}

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});