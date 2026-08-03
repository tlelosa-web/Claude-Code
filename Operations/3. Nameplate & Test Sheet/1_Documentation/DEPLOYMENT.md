# Deployment Guide

## Local Development Setup

### Quick Start (Windows PowerShell)

1. **Navigate to project root:**
   ```powershell
   cd 'C:\Dev\Operations\3. Nameplate & Test Sheet\4_Scripts'
   ```

2. **Start backend server:**
   ```powershell
   cd backend
   & '.\.venv\Scripts\python.exe' -m uvicorn main:app --reload
   ```
   
   Server will run at: `http://127.0.0.1:8000`

3. **In another terminal, start frontend:**
   ```powershell
   cd frontend
   npm run dev
   ```
   
   Frontend will run at: `http://localhost:5173`

4. **Open browser:**
   ```
   http://localhost:5173
   ```

## Production Deployment

### Option 1: Docker Deployment (Recommended)

Create `Dockerfile` in project root:

```dockerfile
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.13-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend/ ./backend/
WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic reportlab pdfplumber gunicorn

# Copy frontend build
COPY --from=frontend-build /app/frontend/dist/ ./static/

EXPOSE 8000

# Serve static files + API
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
```

Build and run:
```bash
docker build -t nameplate-tool .
docker run -p 8000:8000 nameplate-tool
```

### Option 2: Traditional Server Deployment

#### Backend (Python/Gunicorn)

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic reportlab pdfplumber gunicorn
   ```

2. Create systemd service file (`/etc/systemd/system/nameplate-backend.service`):
   ```ini
   [Unit]
   Description=Name Plate Tool Backend
   After=network.target

   [Service]
   Type=notify
   User=www-data
   WorkingDirectory=/var/www/nameplate-tool/backend
   Environment="PATH=/var/www/nameplate-tool/backend/venv/bin"
   ExecStart=/var/www/nameplate-tool/backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable service:
   ```bash
   sudo systemctl enable nameplate-backend
   sudo systemctl start nameplate-backend
   ```

#### Frontend (Node.js or Static)

**Option A: Build as static files**

```bash
cd frontend
npm run build
# Deploy dist/ folder to web server (Nginx, Apache)
```

**Option B: Use Node.js server**

```bash
cd frontend
npm install -g serve
serve -s dist -l 5173
```

### Option 3: Cloud Deployment (AWS/Heroku/Google Cloud)

#### Heroku Deployment

1. Create `Procfile`:
   ```
   web: cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
   ```

2. Deploy:
   ```bash
   heroku login
   heroku create nameplate-tool
   heroku addons:create heroku-postgresql
   git push heroku main
   ```

## Environment Configuration

Create `.env` file in backend root:

```env
# Backend
API_PORT=8000
DEBUG=False

# Frontend (in frontend root)
VITE_API_BASE=http://api.yourdomain.com
```

## SSL/HTTPS Setup (Nginx Reverse Proxy)

Create `/etc/nginx/sites-available/nameplate-tool`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/nameplate-tool/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/nameplate-tool /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Performance Optimization

### Backend
- Use Gunicorn with multiple workers: `-w 4`
- Enable caching for motor data PDF
- Consider using Redis for session management
- Enable Gzip compression

### Frontend
- Build is already optimized with Vite
- Enable HTTP/2 push for critical assets
- Set long cache headers for versioned assets

## Monitoring & Logging

### Backend Logs
```bash
sudo journalctl -u nameplate-backend -f
```

### Frontend Logs (if using Node server)
```bash
pm2 logs frontend
```

## Backup & Maintenance

1. **Backup PDF files:**
   ```bash
   tar -czf nameplate-backups-$(date +%Y%m%d).tar.gz backend/*.pdf
   ```

2. **Update motor data:**
   - Replace the PDF file in `backend/2025 - CTP 022- PB4  Performance Data Rev 0.pdf`
   - Backend will automatically reload data on next request

3. **Dependencies:**
   - Regular `npm update` for frontend
   - Regular `pip update` for backend packages
   - Monitor security advisories

## Troubleshooting Deployment

### 502 Bad Gateway
- Check if backend service is running
- Check Gunicorn/Uvicorn logs
- Verify port 8000 is not blocked

### PDF generation fails
- Verify PDF file exists
- Check file permissions
- Check disk space

### Frontend not loading
- Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Verify dist folder exists
- Check frontend build output

## Support

For issues, check:
1. Application logs
2. Browser console (F12)
3. API response status codes
4. PDF file accessibility
