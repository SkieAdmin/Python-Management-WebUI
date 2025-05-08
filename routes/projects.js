import express from 'express';
import multer from 'multer';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import dotenv from 'dotenv';
import https from 'https';
import child_process from 'child_process';
import { createServer } from 'http';
import { Server } from 'socket.io';
import AdmZip from 'adm-zip';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config();

const router = express.Router();
const projectsDir = process.env.PROJECTS_DIR || path.join(__dirname, '..', 'projects');

// Ensure projects directory exists with proper permissions
if (!fs.existsSync(projectsDir)) {
  try {
    // Create directory with recursive option to create parent directories if needed
    fs.mkdirSync(projectsDir, { recursive: true, mode: 0o777 });
    console.log(`Created projects directory at ${projectsDir}`);
  } catch (error) {
    console.error(`Error creating projects directory: ${error.message}`);
    console.log('Attempting to create directory with relative path as fallback...');
    
    // Fallback to a relative path if absolute path fails
    const fallbackDir = path.join(__dirname, '..', 'projects');
    if (!fs.existsSync(fallbackDir)) {
      fs.mkdirSync(fallbackDir, { recursive: true });
      console.log(`Created fallback projects directory at ${fallbackDir}`);
    }
    
    // Update projectsDir to use the fallback
    process.env.PROJECTS_DIR = fallbackDir;
  }
}

// Configure multer for file upload
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, projectsDir);
  },
  filename: (req, file, cb) => {
    cb(null, `${req.body.lastName}-${Date.now()}${path.extname(file.originalname)}`);
  }
});

const upload = multer({ 
  storage: storage,
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if (ext !== '.zip') {
      return cb(new Error('Only zip files are allowed'));
    }
    cb(null, true);
  }
});

// Project Management Routes
router.get('/', (req, res) => {
  try {
    // Read all JSON metadata files
    const projects = fs.readdirSync(projectsDir)
      .filter(file => path.extname(file) === '.json')
      .map(file => {
        const metadata = JSON.parse(fs.readFileSync(path.join(projectsDir, file), 'utf8'));
        return {
          name: metadata.name,
          fileName: metadata.fileName,
          status: metadata.status,
          port: metadata.port,
          subdomain: metadata.subdomain,
          createdAt: metadata.createdAt
        };
      });
    
    res.render('projects', { projects });
  } catch (error) {
    console.error('Error loading projects:', error);
    res.status(500).render('error', { message: 'Error loading projects' });
  }
});

router.post('/upload', upload.single('projectFile'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).send('No file uploaded.');
    }

    const projectName = req.body.lastName;
    const status = req.body.status || 'Active';
    const port = 3000 + Math.floor(Math.random() * 1000); // Random port between 3000-3999
    
    // Create project directory
    const projectDir = path.join(projectsDir, projectName);
    if (!fs.existsSync(projectDir)) {
      fs.mkdirSync(projectDir, { recursive: true });
    }
    
    // Extract ZIP file
    const zipPath = path.join(projectsDir, req.file.filename);
    const zip = new AdmZip(zipPath);
    
    // Create a clean directory structure without nested duplicates
    // First, check the zip structure
    const zipEntries = zip.getEntries();
    let rootDirs = new Set();
    
    // Get all top-level directories in the zip
    zipEntries.forEach(entry => {
      if (entry.entryName.includes('/')) {
        rootDirs.add(entry.entryName.split('/')[0]);
      }
    });
    
    // If there's only one root directory, extract to that directory
    // to avoid unnecessary nesting
    if (rootDirs.size === 1) {
      const singleRootDir = Array.from(rootDirs)[0];
      console.log(`Zip has single root directory: ${singleRootDir}`);
      
      // Create a temporary extraction directory
      const tempExtractDir = path.join(projectsDir, `temp_${Date.now()}`);
      if (!fs.existsSync(tempExtractDir)) {
        fs.mkdirSync(tempExtractDir, { recursive: true });
      }
      
      // Extract to temp directory first
      zip.extractAllTo(tempExtractDir, true);
      
      // Move contents from the single root directory to the project directory
      const singleRootPath = path.join(tempExtractDir, singleRootDir);
      if (fs.existsSync(singleRootPath) && fs.statSync(singleRootPath).isDirectory()) {
        // Create project directory if it doesn't exist
        if (!fs.existsSync(projectDir)) {
          fs.mkdirSync(projectDir, { recursive: true });
        }
        
        // Copy all files from the single root to the project directory
        fs.readdirSync(singleRootPath).forEach(item => {
          const srcPath = path.join(singleRootPath, item);
          const destPath = path.join(projectDir, item);
          
          if (fs.statSync(srcPath).isDirectory()) {
            // Recursively copy directory
            const copyDirRecursive = (src, dest) => {
              if (!fs.existsSync(dest)) {
                fs.mkdirSync(dest, { recursive: true });
              }
              
              fs.readdirSync(src).forEach(item => {
                const srcItemPath = path.join(src, item);
                const destItemPath = path.join(dest, item);
                
                if (fs.statSync(srcItemPath).isDirectory()) {
                  copyDirRecursive(srcItemPath, destItemPath);
                } else {
                  fs.copyFileSync(srcItemPath, destItemPath);
                }
              });
            };
            
            copyDirRecursive(srcPath, destPath);
          } else {
            fs.copyFileSync(srcPath, destPath);
          }
        });
        
        // Clean up temp directory
        const rimrafSync = (dir) => {
          if (fs.existsSync(dir)) {
            fs.readdirSync(dir).forEach((file) => {
              const curPath = path.join(dir, file);
              if (fs.lstatSync(curPath).isDirectory()) {
                rimrafSync(curPath);
              } else {
                fs.unlinkSync(curPath);
              }
            });
            fs.rmdirSync(dir);
          }
        };
        rimrafSync(tempExtractDir);
      } else {
        // Fallback to direct extraction if structure is unexpected
        zip.extractAllTo(projectDir, true);
      }
    } else {
      // Multiple root directories or flat structure, extract directly
      zip.extractAllTo(projectDir, true);
    }
    
    // Check for requirements.txt and install if exists
    const requirementsPath = path.join(projectDir, 'requirements.txt');
    let requirementsInstalled = false;
    let installationLog = '';
    
    if (fs.existsSync(requirementsPath)) {
      try {
        const installCmd = process.platform === 'win32' 
          ? `pip install -r "${requirementsPath}"` 
          : `pip3 install -r "${requirementsPath}"`;
        
        installationLog = child_process.execSync(installCmd).toString();
        requirementsInstalled = true;
      } catch (err) {
        installationLog = err.toString();
        console.error('Error installing requirements:', err);
      }
    }
    
    // Check if it's a Django project by looking for manage.py
    let isDjango = false;
    let djangoProjectDir = projectDir;
    let mainPythonFile = '';
    
    // First, look for manage.py in the root directory
    if (fs.existsSync(path.join(projectDir, 'manage.py'))) {
      isDjango = true;
      mainPythonFile = 'manage.py';
    } else {
      // Look for manage.py in subdirectories (one level deep)
      const subdirs = fs.readdirSync(projectDir)
        .filter(item => fs.statSync(path.join(projectDir, item)).isDirectory());
      
      for (const subdir of subdirs) {
        const subdirPath = path.join(projectDir, subdir);
        if (fs.existsSync(path.join(subdirPath, 'manage.py'))) {
          isDjango = true;
          djangoProjectDir = subdirPath;
          mainPythonFile = 'manage.py';
          break;
        }
      }
    }
    
    // If not Django, look for other Python files
    if (!isDjango) {
      const pythonFiles = fs.readdirSync(projectDir)
        .filter(file => file.endsWith('.py'));
      
      if (pythonFiles.includes('app.py')) {
        mainPythonFile = 'app.py';
      } else if (pythonFiles.includes('main.py')) {
        mainPythonFile = 'main.py';
      } else if (pythonFiles.length > 0) {
        mainPythonFile = pythonFiles[0];
      }
    }
    
    // Save project metadata
    const projectMetadata = {
      name: projectName,
      fileName: req.file.filename,
      extractedDir: projectDir,
      mainPythonFile: mainPythonFile,
      isDjango: isDjango,
      djangoProjectDir: isDjango ? djangoProjectDir : null,
      status: status,
      port: port,
      createdAt: new Date().toISOString(),
      subdomain: `${projectName.toLowerCase()}.csshub.uk`,
      requirementsInstalled: requirementsInstalled,
      installationLog: installationLog,
      isRunning: false,
      logs: []
    };
    
    const metadataPath = path.join(projectsDir, `${projectName}.json`);
    fs.writeFileSync(metadataPath, JSON.stringify(projectMetadata, null, 2));
    
    // Create Cloudflare subdomain
    if (status === 'Active') {
      await createCloudflareSubdomain(projectName.toLowerCase());
      await createNginxConfig(projectName.toLowerCase(), port);
      
      // Start the Python project if active
      if (mainPythonFile) {
        startPythonProject(projectName, projectDir, mainPythonFile, port);
      }
    }
    
    res.redirect('/projects');
  } catch (error) {
    console.error('Error uploading project:', error);
    res.status(500).render('error', { message: 'Error uploading project' });
  }
});

router.post('/toggle-status/:projectName', async (req, res) => {
  try {
    const { projectName } = req.params;
    const { status } = req.body;
    
    const metadataPath = path.join(projectsDir, `${projectName}.json`);
    
    if (fs.existsSync(metadataPath)) {
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      metadata.status = status;
      fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
      
      // Update Cloudflare and Nginx based on status
      if (status === 'Active') {
        await createCloudflareSubdomain(metadata.name.toLowerCase());
        await createNginxConfig(metadata.name.toLowerCase(), metadata.port);
      } else {
        await deleteCloudflareSubdomain(metadata.name.toLowerCase());
        await deleteNginxConfig(metadata.name.toLowerCase());
      }
    }
    
    res.redirect('/projects');
  } catch (error) {
    console.error('Error toggling project status:', error);
    res.status(500).render('error', { message: 'Error toggling project status' });
  }
});

router.post('/delete/:projectName', async (req, res) => {
  const { projectName } = req.params;
  
  try {
    const metadataPath = path.join(projectsDir, `${projectName}.json`);
    
    if (fs.existsSync(metadataPath)) {
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      const zipFile = path.join(projectsDir, metadata.fileName);
      
      // Kill any running process
      if (metadata.processId) {
        try {
          process.kill(metadata.processId);
        } catch (err) {
          console.log('No process to kill or already terminated');
        }
      }
      
      // Delete files
      if (fs.existsSync(zipFile)) {
        fs.unlinkSync(zipFile);
      }
      
      // Delete project directory if it exists
      if (metadata.extractedDir && fs.existsSync(metadata.extractedDir)) {
        // Use rimraf or fs-extra to delete directory recursively
        try {
          const rimrafSync = (dir) => {
            if (fs.existsSync(dir)) {
              fs.readdirSync(dir).forEach((file) => {
                const curPath = path.join(dir, file);
                if (fs.lstatSync(curPath).isDirectory()) {
                  rimrafSync(curPath);
                } else {
                  fs.unlinkSync(curPath);
                }
              });
              fs.rmdirSync(dir);
            }
          };
          rimrafSync(metadata.extractedDir);
        } catch (err) {
          console.error('Error deleting directory:', err);
        }
      }
      
      fs.unlinkSync(metadataPath);
      
      // Remove Cloudflare subdomain and Nginx config
      await deleteCloudflareSubdomain(metadata.name.toLowerCase());
      await deleteNginxConfig(metadata.name.toLowerCase());
      
      res.redirect('/projects');
    } else {
      res.status(404).render('error', { message: 'Project not found' });
    }
  } catch (error) {
    console.error('Error deleting project:', error);
    res.status(500).render('error', { message: 'Error deleting project' });
  }
});

// Cloudflare API functions
async function createCloudflareSubdomain(subdomain) {
  const apiKey = process.env.CLOUDFLARE_API_KEY;
  const email = process.env.CLOUDFLARE_EMAIL;
  const zoneId = process.env.CLOUDFLARE_ZONE_ID;
  
  if (!apiKey || !email || !zoneId) {
    throw new Error('Cloudflare API credentials not configured');
  }
  
  // Get the server's public IP or use environment variable
  let serverIP = process.env.SERVER_IP;
  
  // If SERVER_IP is not set in environment variables, try to detect it
  if (!serverIP) {
    try {
      // This is a simple way to get the server's IP, but not 100% reliable
      // Better to set it explicitly in .env file
      const { networkInterfaces } = require('os');
      const nets = networkInterfaces();
      
      // Try to find a non-internal IPv4 address
      for (const name of Object.keys(nets)) {
        for (const net of nets[name]) {
          // Skip internal and non-IPv4 addresses
          if (net.family === 'IPv4' && !net.internal) {
            serverIP = net.address;
            break;
          }
        }
        if (serverIP) break;
      }
    } catch (err) {
      console.error('Error detecting server IP:', err);
    }
  }
  
  // If we still don't have an IP, use a fallback
  if (!serverIP) {
    console.warn('WARNING: Could not detect server IP. Using fallback IP. Please set SERVER_IP in .env file.');
    serverIP = '1.1.1.1'; // This is a fallback and should be replaced with your actual VPS IP
  }
  
  const data = JSON.stringify({
    type: 'A',
    name: subdomain,
    content: serverIP,
    ttl: 1,
    proxied: true
  });
  
  const options = {
    hostname: 'api.cloudflare.com',
    path: `/client/v4/zones/${zoneId}/dns_records`,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Auth-Email': email,
      'X-Auth-Key': apiKey
    }
  };
  
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        const response = JSON.parse(responseData);
        if (response.success) {
          resolve(response.result);
        } else {
          reject(new Error(`Cloudflare API error: ${JSON.stringify(response.errors)}`));
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    req.write(data);
    req.end();
  });
}

async function deleteCloudflareSubdomain(subdomain) {
  const apiKey = process.env.CLOUDFLARE_API_KEY;
  const email = process.env.CLOUDFLARE_EMAIL;
  const zoneId = process.env.CLOUDFLARE_ZONE_ID;
  
  if (!apiKey || !email || !zoneId) {
    throw new Error('Cloudflare API credentials not configured');
  }
  
  // First, find the DNS record ID
  const recordId = await getCloudflareRecordId(subdomain);
  
  if (!recordId) {
    return; // Record doesn't exist, nothing to delete
  }
  
  const options = {
    hostname: 'api.cloudflare.com',
    path: `/client/v4/zones/${zoneId}/dns_records/${recordId}`,
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'X-Auth-Email': email,
      'X-Auth-Key': apiKey
    }
  };
  
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        const response = JSON.parse(responseData);
        if (response.success) {
          resolve(response.result);
        } else {
          reject(new Error(`Cloudflare API error: ${JSON.stringify(response.errors)}`));
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    req.end();
  });
}

async function getCloudflareRecordId(subdomain) {
  const apiKey = process.env.CLOUDFLARE_API_KEY;
  const email = process.env.CLOUDFLARE_EMAIL;
  const zoneId = process.env.CLOUDFLARE_ZONE_ID;
  
  const options = {
    hostname: 'api.cloudflare.com',
    path: `/client/v4/zones/${zoneId}/dns_records?name=${subdomain}.csshub.uk`,
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-Auth-Email': email,
      'X-Auth-Key': apiKey
    }
  };
  
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        const response = JSON.parse(responseData);
        if (response.success) {
          if (response.result.length > 0) {
            resolve(response.result[0].id);
          } else {
            resolve(null); // No record found
          }
        } else {
          reject(new Error(`Cloudflare API error: ${JSON.stringify(response.errors)}`));
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    req.end();
  });
}

// Nginx configuration functions
async function createNginxConfig(subdomain, port) {
  const configPath = process.env.NGINX_CONFIG_PATH || '/etc/nginx/sites-available/';
  const configContent = `server {
    listen 80;
    server_name ${subdomain}.csshub.uk;

    location / {
        proxy_pass http://localhost:${port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
`;
  
  // On Windows, we'll just create the config file without actually applying it
  // In production on Ubuntu, you'd use these commands
  if (process.platform === 'win32') {
    const configDir = path.join(__dirname, '..', 'nginx-configs');
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir);
    }
    fs.writeFileSync(path.join(configDir, `${subdomain}.conf`), configContent);
  } else {
    // For Linux/Ubuntu
    fs.writeFileSync(`${configPath}${subdomain}.conf`, configContent);
    
    // Create symlink and reload nginx
    try {
      child_process.execSync(`ln -sf ${configPath}${subdomain}.conf /etc/nginx/sites-enabled/`);
      child_process.execSync('systemctl reload nginx');
    } catch (error) {
      console.error('Error reloading Nginx:', error);
    }
  }
}

async function deleteNginxConfig(subdomain) {
  const configPath = process.env.NGINX_CONFIG_PATH || '/etc/nginx/sites-available/';
  
  if (process.platform === 'win32') {
    const configFile = path.join(__dirname, '..', 'nginx-configs', `${subdomain}.conf`);
    if (fs.existsSync(configFile)) {
      fs.unlinkSync(configFile);
    }
  } else {
    // For Linux/Ubuntu
    try {
      // Remove config and symlink
      if (fs.existsSync(`${configPath}${subdomain}.conf`)) {
        fs.unlinkSync(`${configPath}${subdomain}.conf`);
      }
      
      if (fs.existsSync(`/etc/nginx/sites-enabled/${subdomain}.conf`)) {
        fs.unlinkSync(`/etc/nginx/sites-enabled/${subdomain}.conf`);
      }
      
      // Reload nginx
      child_process.execSync('systemctl reload nginx');
    } catch (error) {
      console.error('Error removing Nginx config:', error);
    }
  }
}

// Start Python project
function startPythonProject(projectName, projectDir, mainPythonFile, port) {
  try {
    const metadataPath = path.join(projectsDir, `${projectName}.json`);
    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
    
    // Kill existing process if running
    if (metadata.processId) {
      try {
        process.kill(metadata.processId);
      } catch (err) {
        console.log('No process to kill or already terminated');
      }
    }
    
    // Command to run Python with port as environment variable
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    let cmd;
    let workingDir = projectDir;
    
    // Special handling for Django projects
    if (metadata.isDjango && metadata.mainPythonFile === 'manage.py') {
      workingDir = metadata.djangoProjectDir || projectDir;
      
      // Double-check that manage.py exists in the working directory
      const managePyPath = path.join(workingDir, 'manage.py');
      if (!fs.existsSync(managePyPath)) {
        console.error(`Error: manage.py not found at ${managePyPath}`);
        
        // Try to find manage.py anywhere in the project directory
        const findManagePy = (dir, depth = 0, maxDepth = 3) => {
          if (depth > maxDepth) return null;
          
          const files = fs.readdirSync(dir);
          
          // Check if manage.py exists in this directory
          if (files.includes('manage.py')) {
            return dir;
          }
          
          // Check subdirectories
          for (const file of files) {
            const filePath = path.join(dir, file);
            if (fs.statSync(filePath).isDirectory()) {
              const result = findManagePy(filePath, depth + 1, maxDepth);
              if (result) return result;
            }
          }
          
          return null;
        };
        
        const foundDir = findManagePy(projectDir);
        if (foundDir) {
          console.log(`Found manage.py in ${foundDir}`);
          workingDir = foundDir;
          
          // Update metadata for future runs
          const metadataPath = path.join(projectsDir, `${metadata.name}.json`);
          if (fs.existsSync(metadataPath)) {
            const updatedMetadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
            updatedMetadata.djangoProjectDir = foundDir;
            fs.writeFileSync(metadataPath, JSON.stringify(updatedMetadata, null, 2));
          }
        } else {
          console.error('Could not find manage.py anywhere in the project directory');
        }
      }
      
      cmd = `${pythonCmd} "${path.join(workingDir, 'manage.py')}" runserver 0.0.0.0:${port}`;
      console.log(`Starting Django project on port ${port} in directory ${workingDir}`);
    } else {
      cmd = `${pythonCmd} "${path.join(projectDir, mainPythonFile)}"`;
    }
    
    // Spawn process with environment variable for port
    const env = { ...process.env, PORT: port.toString() };
    const pythonProcess = child_process.spawn(cmd, {
      cwd: workingDir,
      env: env,
      shell: true
    });
    
    // Update metadata with process ID
    metadata.processId = pythonProcess.pid;
    metadata.isRunning = true;
    metadata.logs = [];
    fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
    
    // Handle stdout
    pythonProcess.stdout.on('data', (data) => {
      const logData = data.toString();
      console.log(`[${projectName}] ${logData}`);
      
      // Update logs in metadata (keep last 100 lines)
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      metadata.logs.push({
        timestamp: new Date().toISOString(),
        type: 'stdout',
        message: logData
      });
      
      if (metadata.logs.length > 100) {
        metadata.logs = metadata.logs.slice(-100);
      }
      
      fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
    });
    
    // Handle stderr
    pythonProcess.stderr.on('data', (data) => {
      const logData = data.toString();
      console.error(`[${projectName}] Error: ${logData}`);
      
      // Update logs in metadata (keep last 100 lines)
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      metadata.logs.push({
        timestamp: new Date().toISOString(),
        type: 'stderr',
        message: logData
      });
      
      if (metadata.logs.length > 100) {
        metadata.logs = metadata.logs.slice(-100);
      }
      
      fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
    });
    
    // Handle process exit
    pythonProcess.on('close', (code) => {
      console.log(`[${projectName}] Process exited with code ${code}`);
      
      // Update metadata to show process is not running
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      metadata.isRunning = false;
      metadata.logs.push({
        timestamp: new Date().toISOString(),
        type: 'system',
        message: `Process exited with code ${code}`
      });
      
      if (metadata.logs.length > 100) {
        metadata.logs = metadata.logs.slice(-100);
      }
      
      fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
    });
    
    return pythonProcess.pid;
  } catch (error) {
    console.error(`Error starting Python project ${projectName}:`, error);
    return null;
  }
}

// Add new routes for project management
router.get('/logs/:projectName', (req, res) => {
  try {
    const { projectName } = req.params;
    const metadataPath = path.join(projectsDir, `${projectName}.json`);
    
    if (fs.existsSync(metadataPath)) {
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      res.render('logs', { project: metadata });
    } else {
      res.status(404).render('error', { message: 'Project not found' });
    }
  } catch (error) {
    console.error('Error loading project logs:', error);
    res.status(500).render('error', { message: 'Error loading project logs' });
  }
});

// Route to run custom pip install commands
router.post('/run-command/:projectName', async (req, res) => {
  try {
    const { projectName } = req.params;
    const { command } = req.body;
    const metadataPath = path.join(projectsDir, `${projectName}.json`);
    
    if (!fs.existsSync(metadataPath)) {
      return res.status(404).json({ success: false, message: 'Project not found' });
    }
    
    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
    const workingDir = metadata.isDjango ? (metadata.djangoProjectDir || metadata.extractedDir) : metadata.extractedDir;
    
    // Validate command (only allow pip install commands for security)
    if (!command.trim().startsWith('pip install') && !command.trim().startsWith('pip3 install')) {
      return res.json({ success: false, message: 'Only pip install commands are allowed for security reasons' });
    }
    
    console.log(`Running command for ${projectName}: ${command}`);
    
    // Execute the command
    const cmdOutput = await new Promise((resolve) => {
      child_process.exec(command, { cwd: workingDir }, (error, stdout, stderr) => {
        if (error) {
          console.error(`Command execution error: ${error.message}`);
          resolve({ success: false, output: stderr || error.message });
        } else {
          resolve({ success: true, output: stdout });
        }
      });
    });
    
    // Add command output to logs
    metadata.logs.push({
      timestamp: new Date().toISOString(),
      type: cmdOutput.success ? 'stdout' : 'stderr',
      message: `Command: ${command}\n${cmdOutput.output}`
    });
    
    // Keep only the last 100 log entries
    if (metadata.logs.length > 100) {
      metadata.logs = metadata.logs.slice(-100);
    }
    
    // Update metadata
    fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
    
    res.json(cmdOutput);
  } catch (error) {
    console.error('Error running command:', error);
    res.status(500).json({ success: false, message: 'Error running command' });
  }
});

router.post('/start/:projectName', async (req, res) => {
  try {
    const { projectName } = req.params;
    const metadataPath = path.join(projectsDir, `${projectName}.json`);
    
    if (fs.existsSync(metadataPath)) {
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      
      if (!metadata.isRunning && metadata.mainPythonFile) {
        startPythonProject(
          projectName, 
          metadata.extractedDir, 
          metadata.mainPythonFile, 
          metadata.port
        );
        res.redirect(`/projects/logs/${projectName}`);
      } else {
        res.redirect('/projects');
      }
    } else {
      res.status(404).render('error', { message: 'Project not found' });
    }
  } catch (error) {
    console.error('Error starting project:', error);
    res.status(500).render('error', { message: 'Error starting project' });
  }
});

router.post('/stop/:projectName', async (req, res) => {
  try {
    const { projectName } = req.params;
    const metadataPath = path.join(projectsDir, `${projectName}.json`);
    
    if (fs.existsSync(metadataPath)) {
      const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
      
      if (metadata.isRunning && metadata.processId) {
        try {
          process.kill(metadata.processId);
          
          // Update metadata
          metadata.isRunning = false;
          metadata.logs.push({
            timestamp: new Date().toISOString(),
            type: 'system',
            message: 'Process stopped by user'
          });
          
          fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
        } catch (err) {
          console.error('Error stopping process:', err);
        }
      }
      
      res.redirect('/projects');
    } else {
      res.status(404).render('error', { message: 'Project not found' });
    }
  } catch (error) {
    console.error('Error stopping project:', error);
    res.status(500).render('error', { message: 'Error stopping project' });
  }
});

export default router;
