# Python Project Manager

## Features
- User Authentication
- Project Upload
- Project Status Management
- Cloudflare Subdomain Integration
- Nginx Configuration Management

## Prerequisites
- Node.js (v16+)
- npm
- Cloudflare API Access
- Nginx

## Setup
1. Clone the repository
2. Install dependencies: `npm install`
3. Configure `.env` file with your Cloudflare and Nginx settings
4. Run the application: `npm start`

## Login Credentials
- Username: admin
- Password: gocotano2025

## Deployment Workflow
1. Upload Python project as ZIP
2. Specify project name (Last Name)
3. Choose Active/Inactive status
4. System will:
   - Create Cloudflare subdomain
   - Configure Nginx
   - Manage project lifecycle

## Security Notes
- Change default credentials
- Secure your `.env` file
- Use HTTPS in production
