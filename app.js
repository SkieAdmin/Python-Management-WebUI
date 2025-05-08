import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import fs from 'fs';
import child_process from 'child_process';
import projectsRouter from './routes/projects.js';

// ES6 module equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const projectsDir = process.env.PROJECTS_DIR || path.join(__dirname, 'public', 'python');

// Create HTTP server and Socket.io instance
const httpServer = createServer(app);
const io = new SocketIOServer(httpServer);

// View engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Make io available to routes
app.set('io', io);

// Socket.io setup
io.on('connection', (socket) => {
  console.log('Client connected');
  
  socket.on('join', (projectName) => {
    console.log(`Client joined room: ${projectName}`);
    socket.join(projectName);
  });
  
  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

// Helper function to start a Python project
global.startPythonProject = (projectName, projectDir, mainPythonFile, port) => {
  const metadataPath = path.join(projectsDir, `${projectName}.json`);
  
  if (!fs.existsSync(metadataPath)) {
    console.error(`Metadata file not found for project: ${projectName}`);
    return;
  }
  
  const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
  const workingDir = metadata.isDjango ? (metadata.djangoProjectDir || projectDir) : projectDir;
  
  // Command to run based on project type
  let command = '';
  if (metadata.isDjango) {
    command = `python ${mainPythonFile} runserver 0.0.0.0:${port}`;
  } else {
    command = `python ${mainPythonFile}`;
  }
  
  console.log(`Starting project: ${projectName}`);
  console.log(`Command: ${command}`);
  console.log(`Working directory: ${workingDir}`);
  
  // Start the process
  const process = child_process.spawn('python', 
    metadata.isDjango ? 
      [mainPythonFile, 'runserver', `0.0.0.0:${port}`] : 
      [mainPythonFile], 
    { cwd: workingDir }
  );
  
  // Update metadata
  metadata.isRunning = true;
  metadata.processId = process.pid;
  metadata.logs = metadata.logs || [];
  metadata.logs.push({
    timestamp: new Date().toISOString(),
    type: 'system',
    message: `Process started with PID ${process.pid}`
  });
  
  fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
  
  // Handle process output
  process.stdout.on('data', (data) => {
    const logEntry = {
      timestamp: new Date().toISOString(),
      type: 'stdout',
      message: data.toString()
    };
    
    // Add to logs
    metadata.logs.push(logEntry);
    
    // Keep only the last 100 log entries
    if (metadata.logs.length > 100) {
      metadata.logs = metadata.logs.slice(-100);
    }
    
    fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
    
    // Emit to socket.io clients
    io.to(projectName).emit('log', logEntry);
  });
  
  process.stderr.on('data', (data) => {
    const logEntry = {
      timestamp: new Date().toISOString(),
      type: 'stderr',
      message: data.toString()
    };
    
    // Add to logs
    metadata.logs.push(logEntry);
    
    // Keep only the last 100 log entries
    if (metadata.logs.length > 100) {
      metadata.logs = metadata.logs.slice(-100);
    }
    
    fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
    
    // Emit to socket.io clients
    io.to(projectName).emit('log', logEntry);
  });
  
  process.on('close', (code) => {
    const logEntry = {
      timestamp: new Date().toISOString(),
      type: 'system',
      message: `Process exited with code ${code}`
    };
    
    // Update metadata
    metadata.isRunning = false;
    metadata.processId = null;
    metadata.logs.push(logEntry);
    
    fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));
    
    // Emit to socket.io clients
    io.to(projectName).emit('log', logEntry);
  });
  
  return process;
};

// Routes
app.use('/projects', projectsRouter);

// Home route
app.get('/', (req, res) => {
  res.redirect('/projects');
});

// 404 handler
app.use((req, res) => {
  res.status(404).render('error', { message: 'Page not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).render('error', { message: err.message || 'Something went wrong!' });
});

// Start server
httpServer.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

export default app;
