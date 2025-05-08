# Python Management WebUI

A web-based user interface for managing Python Django projects. This application allows you to upload, deploy, and manage multiple Python projects through a user-friendly web interface.

## Features

- **Project Management**: Upload, start, stop, and delete Python projects
- **Django Support**: Automatic detection of Django projects with manage.py
- **Subdomain Configuration**: Automatically configure subdomains for each project
- **Nginx Integration**: Configure Nginx to proxy requests to your Python applications
- **Cloudflare Integration**: Automatically create DNS records for your subdomains
- **Real-time Logs**: View application logs in real-time
- **Command Execution**: Run pip install commands on your projects

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Python (for running the managed projects)
- Nginx (for proxying requests)
- Cloudflare account (for DNS management)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Python-Management-WebUI.git
   cd Python-Management-WebUI
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Configure environment variables:
   Copy the `.env.example` file to `.env` and update the values:
   ```
   cp .env.example .env
   ```

   Required environment variables:
   - `PORT`: The port for the web UI (default: 3032)
   - `PROJECTS_DIR`: Directory to store project metadata
   - `CLOUDFLARE_API_KEY`: Your Cloudflare API key
   - `CLOUDFLARE_EMAIL`: Your Cloudflare email
   - `CLOUDFLARE_ZONE_ID`: Your Cloudflare zone ID
   - `NGINX_CONFIG_PATH`: Path to Nginx sites-available directory
   - `SERVER_IP`: Your server's public IP address
   - `DOMAIN`: Your domain for subdomains (e.g., ccshub.uk)

4. Start the application:
   ```
   npm start
   ```

   For development with auto-restart:
   ```
   npm run dev
   ```

5. Access the web UI at http://localhost:3032 (or the port you configured)

## Usage

### Adding a New Project

1. Click "Add New Project" on the projects page
2. Enter a project name (this will be used for the subdomain)
3. Upload a ZIP file containing your Python Django project
4. Set the initial status (Active/Inactive)
5. Click "Upload Project"

### Managing Projects

- **Start/Stop**: Use the Start/Stop buttons to control the project's server
- **View**: Open the project in a new tab
- **Logs**: View the project's logs in real-time
- **Toggle Status**: Enable or disable the project
- **Run Command**: Execute pip install commands on the project
- **Delete**: Remove the project completely

## Project Structure

- `app.js`: Main application entry point
- `routes/projects.js`: Project management routes
- `views/`: EJS templates for the web UI
- `public/`: Static files and uploaded projects
- `public/python/`: Directory where Python projects are stored

## License

MIT
