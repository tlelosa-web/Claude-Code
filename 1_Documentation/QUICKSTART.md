# Quick Start Guide - Name Plate Tool

## For Windows Users (PowerShell)

### First Time Setup (One-time)

```powershell
# 1. Navigate to project
cd '<project-root>'

# 2. Create and activate virtual environment for backend
python -m venv .venv
.venv\Scripts\Activate.ps1
cd 4_Scripts\backend

# 3. Install backend dependencies
pip install -r requirements.txt
cd ..\..

# 4. Install frontend dependencies
cd 4_Scripts\frontend
npm install
cd ..\..

# Done! Now use startup instructions below
```

### Daily Startup (Run this each time you want to use the app)

**Terminal 1 - Backend Server:**

```powershell
cd '<project-root>'
.venv\Scripts\Activate.ps1
cd 4_Scripts\backend
python -m uvicorn main:app --reload
```

**Terminal 2 - Frontend Server:**

```powershell
cd '<project-root>\4_Scripts\frontend'
npm run dev
```

### Open in Browser on Windows

```text
http://localhost:5173
```

---

## For Linux/macOS Users

### First Time Setup

```bash
# 1. Navigate to project
cd ~/NamePlateTool

# 2. Create and activate virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt
cd ..

# 4. Install frontend dependencies
cd frontend
npm install
cd ..
```

### Daily Startup

**Terminal 1 - Backend:**

```bash
cd ~/NamePlateTool/backend
source .venv/bin/activate
python -m uvicorn main:app --reload
```

**Terminal 2 - Frontend:**

```bash
cd ~/NamePlateTool/frontend
npm run dev
```

### Open in Browser on Linux/macOS

```text
http://localhost:5173
```

---

## Common Tasks

### Generate Production Build

```bash
cd frontend
npm run build
# Output: frontend/dist folder (ready to deploy)
```

### Stop Servers

- **Backend**: Press `Ctrl+C` in backend terminal
- **Frontend**: Press `Ctrl+C` in frontend terminal

### Reset Everything

```bash
# Remove node_modules
cd frontend
rm -r node_modules
npm install

# Reset Python environment
cd backend
rm -r .venv
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

### Check if Server is Running

```bash
# Backend (should return JSON)
curl http://127.0.0.1:8000/api/speed?pole=4

# Frontend (should show HTML)
curl http://localhost:5173
```

---

## Form Fields Explained

| Field | Required | Auto-filled | Notes |
| ----- | -------- | ----------- | ----- |
| Series | No | No | e.g., IE3, Premium Efficiency |
| Motor (kW) | Yes | No | Motor power in kilowatts |
| Pole | Yes | No | Must select 2, 4, 6, or 8 |
| Voltage | Yes | No | Usually 380V, 525V, or 220V |
| F.L.A | No | Yes | Auto-calculated if left blank |
| Op Speed | - | Yes | Auto-calculated from pole |
| Connection | - | Yes | Auto-calculated (STAR/DELTA) |
| Size | No | No | Frame size, e.g., 90, 100 |
| Class/Pitch | No | No | Insulation class, e.g., Class F |
| Phase | No | No | Usually 3~ for three-phase |
| Frequency | No | No | Usually 50 Hz or 60 Hz |
| Date of Manuf | No | No | e.g., JAN.2025, FEB.2024 |
| Serial No | No | No | Motor serial number |
| Op Temp | No | Yes | Operating temperature, default 20 C |

---

## Troubleshooting

### Error: "Import could not be resolved"

**Solution:** Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Error: "Cannot find module 'react'"

**Solution:** Install frontend dependencies

```bash
cd frontend
npm install
```

### Error: "Connection refused" when opening localhost

**Solution:**

- Make sure backend is running on another terminal.
- Make sure frontend is running. It should show `Local: http://localhost:5173`.
- Check if port 5173 is already in use.

### Error: "PDF generation failed"

**Solution:**

- Check that the performance data PDF exists in the backend directory.
- Restart backend server.
- Check all form fields are filled correctly.

### Backend won't start - Address already in use

**Solution:** Port 8000 is already in use

```bash
# Find process using port 8000 and kill it
# Windows:
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process

# Linux/macOS:
lsof -ti:8000 | xargs kill -9
```

---

## Keyboard Shortcuts

- **Ctrl+C** - Stop a running server
- **F12** - Open browser developer tools for debugging
- **Ctrl+R** - Reload page, frontend changes auto-reload
- **Ctrl+Shift+Delete** - Clear browser cache if having issues

---

## Getting Help

1. Check browser console with F12 for JavaScript errors.
2. Check backend terminal for API errors.
3. Check CORS settings if getting "blocked by CORS" error.
4. Review README.md for detailed API documentation.
5. Check DEPLOYMENT.md for production setup help.

---

**Happy nameplate generating!**
