# Documentation Summary

This summary captures the authoritative project context from the repository markdown files.

## Project Purpose

The repository implements a motor nameplate and test record sheet generator application. It combines a FastAPI backend with a React + Vite frontend to calculate motor performance values, determine connection types, and generate PDF nameplates.

## Primary Architecture

- Backend: `4_Scripts/backend`
- Frontend: `4_Scripts/frontend`
- Raw input data: `2_Source_Data/raw_sources`
- Generated outputs: `3_Live_Reports`
- Documentation: `1_Documentation`
- Archive/debug artifacts: `5_Archive_and_Debug`

## Core Functionality

- Motor speed calculation from pole count
- Full Load Amperage (FLA) lookup/calculation
- STAR/DELTA connection determination
- PDF nameplate generation
- Real-time frontend validation and preview

## Installation and Setup

### Backend

- Requires Python 3.13+
- Install dependencies with `pip install -r requirements.txt`
- Recommended to create and activate a virtual environment

### Frontend

- Requires Node.js 16+ and npm/yarn
- Install dependencies with `npm install`

## Run Workflow

### Development

- Start backend from `4_Scripts/backend`:
  - `python -m uvicorn main:app --reload`
- Start frontend from `4_Scripts/frontend`:
  - `npm run dev`
- Access UI at `http://localhost:5173`

### Production

- Frontend build via `npm run build`
- Backend can be deployed with Gunicorn/Uvicorn or Docker

## API Endpoints

- `GET /api/speed` — returns motor operating speed from pole count
- `GET /api/fla` — calculates motor Full Load Amperage based on kW, pole count, and voltage
- `GET /api/connection` — determines STAR/DELTA connection type
- `POST /api/generate-pdf` — generates the motor nameplate PDF

## Deployment Guidance

The deployment documentation includes:

- Local development configuration
- Docker deployment example with a multi-stage build
- Traditional Gunicorn deployment
- Heroku deployment notes
- Nginx reverse proxy configuration for frontend and API
- Suggested environment variables for backend and frontend

## Project Governance and Standards

- `1_Documentation/GEMINI.md` describes a 5-folder agentic architecture, a strict modular workflow, and coding standards for safe data handling, logging, and error management.
- `1_Documentation/doe_multi_agent_team_markdown_suite.md` defines a multi-agent coordination model with roles for project management, frontend, backend, DevOps, and QA.

## Recommended Focus Areas

- Verify the actual codebase paths match deployment documentation, especially `4_Scripts/backend` and `4_Scripts/frontend`.
- Treat `1_Documentation/GEMINI.md` as the authoritative architecture directive for repo-level structure and workflow.
- Prefer project-specific docs (`README.md`, `USER_GUIDE.md`, `QUICKSTART.md`, `DEPLOYMENT.md`) over generic template docs.

## Notes

- `4_Scripts/frontend/README.md` is a generic React + Vite template reference and not specific to the Name Plate Tool application.
- There are no dedicated markdown directories such as `docs/`, `architecture/`, or `workflows/` in this workspace.
