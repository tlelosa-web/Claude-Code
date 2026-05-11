# Name Plate Tool

A full-stack web application for generating motor nameplate PDFs with automatic calculations for electrical motor specifications.

## Features

- **Web-based interface** using React + Vite
- **FastAPI backend** with automatic calculations
- **PDF generation** with customizable nameplate layouts
- **Real-time validation** of motor specifications
- **Auto-calculation** of:
  - Operating Speed (from pole count)
  - Full Load Amperage (FLA) (from motor kW and pole count)
  - Connection type (STAR/DELTA) based on voltage, poles, and kW
  - Maximum speed

## Project Structure

```
ProjectRoot/
├── 1_Documentation/
│   ├── GEMINI.md
│   └── USER_GUIDE.md
├── 2_Source_Data/
│   └── raw_sources/                     # Motor PDF and Excel source files
├── 3_Live_Reports/
│   ├── backend_pdfs/                   # Generated PDF outputs
│   └── output/                         # Report templates and generated overlays
├── 4_Scripts/
│   ├── backend/                        # FastAPI and PDF generator code
│   └── frontend/                       # React + Vite application
└── 5_Archive_and_Debug/                # Legacy docs and archived experiments
```

## Requirements

### Backend
- Python 3.13+
- FastAPI
- Uvicorn
- Pydantic
- ReportLab (PDF generation)
- pdfplumber (PDF data extraction)

### Frontend
- Node.js 16+
- npm or yarn

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd 4_Scripts/backend
```

2. Create a virtual environment (if not already done):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - **Windows (PowerShell):**
     ```bash
     venv\Scripts\Activate.ps1
     ```
   - **Linux/macOS:**
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd 4_Scripts/frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Start the Backend Server

```bash
cd 4_Scripts/backend
python -m uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### Start the Frontend Development Server

In a new terminal:

```bash
cd 4_Scripts/frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

The application is now ready to use. Open your browser to `http://localhost:5173`

## API Endpoints

### GET `/api/speed`
Get operating speed based on pole count.

**Parameters:**
- `pole` (string): 2, 4, 6, or 8

**Response:**
```json
{
  "op_speed": "1440",
  "error": null
}
```

### GET `/api/fla`
Calculate Full Load Amperage (FLA).

**Parameters:**
- `motor_kw` (string): Motor power in kW
- `pole` (string): Pole count (2, 4, 6, or 8)
- `voltage` (string): Voltage (380, 525, or 220)

**Response:**
```json
{
  "fla": "2.8",
  "error": null
}
```

### GET `/api/connection`
Determine connection type (STAR/DELTA).

**Parameters:**
- `motor_kw` (string): Motor power in kW
- `pole` (string): Pole count (2, 4, 6, or 8)
- `voltage` (string): Voltage (380, 525, or 220)

**Response:**
```json
{
  "connection": "STAR",
  "error": null
}
```

### POST `/api/generate-pdf`
Generate the motor nameplate PDF.

**Request Body:**
```json
{
  "series": "IE3",
  "class_pitch": "Class F",
  "motor": "1.5",
  "pole": "4",
  "voltage": "380",
  "fla": "2.8",
  "op_temp": "20",
  "serial_no": "ABC123456",
  "size": "90",
  "op_speed": "1440",
  "phase": "3~",
  "frequency": "50",
  "connection": "STAR",
  "date_of_manuf": "JAN.2025",
  "relube_interval": "N/A"
}
```

**Response:** PDF file download

## Building for Production

### Frontend Build

```bash
cd frontend
npm run build
```

The optimized production build will be in the `frontend/dist` directory.

To preview the production build:
```bash
npm run preview
```

### Backend Deployment

For production, use a production ASGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

## Key Features Explained

### Motor Speed Calculation
Operating speed is determined from the pole count using the formula:
- Speed (rpm) = (120 × frequency) / poles
- For 50 Hz:
  - 2-pole: 2880 rpm
  - 4-pole: 1440 rpm
  - 6-pole: 960 rpm
  - 8-pole: 720 rpm

### Connection Type Logic
- **380V STAR**: Up to 3.0 kW for 2/4-pole, 1.5 kW for 6-pole, 1.1 kW for 8-pole
- **380V DELTA**: From 4.0 kW for 2/4-pole, 2.2 kW for 6-pole, 1.5 kW for 8-pole
- **525V & 220V**: DELTA only, with limits per pole

### FLA Calculation
Full Load Amperage is looked up from the motor performance data PDF based on:
- Motor power (kW)
- Pole count
- Voltage

## Troubleshooting

### "Import could not be resolved" errors
Install missing packages:
```bash
pip install fastapi pydantic uvicorn reportlab pdfplumber
```

### Frontend not connecting to backend
- Verify the backend is running on `http://127.0.0.1:8000`
- Check CORS settings in `backend/main.py` include your frontend URL
- Check browser console for API errors

### PDF generation fails
- Ensure the motor performance PDF file exists at: `backend/2025 - CTP 022- PB4  Performance Data Rev 0.pdf`
- Check that reportlab is installed: `pip install reportlab`

## Development

### Code Structure

**Backend (FastAPI):**
- `main.py` - FastAPI app, CORS setup, API endpoints
- `pdf_generator.py` - PDF layout and generation
- `motor_fla_lookup.py` - PDF data extraction for FLA lookup
- `connection_lookup.py` - Connection determination logic

**Frontend (React):**
- `App.jsx` - Main component with form and API calls
- `App.css` - Styling
- Form state management and validation

## Version History

- **v0.4.0** - Full-stack implementation with React frontend and FastAPI backend

## License

Proprietary - Fan Movement (Pty) Ltd
