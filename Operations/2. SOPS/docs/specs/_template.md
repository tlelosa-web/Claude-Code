## Task: Run the Works‑Order & B.O.M System

**Domain:** Software / AI
**Goal:** Start the web‑based Works‑Order & B.O.M application locally and verify basic functionality.
**Inputs:** Source code in the repository, Node .js ≥ 18, npm packages.
**Outputs:**  

- Local dev server at `http://localhost:3000`  
- Log file `logs/run.log`  
- Confirmation that the home page loads without errors.
**Constraints:**  
- Must use the existing `package.json`.  
- No placeholder code – all UI components must be styled per the design system.  
- All commands run via `npm` scripts.
**Acceptance Criteria:**  
- `npm run dev` starts without errors.  
- Browser shows the home page with the “Works Order” dashboard visible.  
- No console warnings in Chrome/Edge.  
**Out of Scope:** Production deployment, database migrations.
