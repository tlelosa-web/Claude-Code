import React, { useState, useEffect } from "react";
import LivePreview from "./components/LivePreview";
import "./App.css";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").trim();

function Field({ label, value, onChange, disabled, placeholder }) {
  return (
    <div className="field-container">
      <label className="field-label">{label}</label>
      <input
        className="field-input"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
      />
    </div>
  );
}

export default function App() {
  const [formData, setFormData] = useState({
    customer_name: "",
    series: "", class_pitch: "", motor: "", pole: "", voltage: "", 
    fla: "", op_temp: "20", serial_no: "", size: "", op_speed: "", 
    phase: "3", frequency: "50", connection: "", date_of_manuf: "", relube_interval: "N/A",
    max_speed: "",
    manufacturer: ""
  });

  const [errors, setErrors] = useState({ customer_name: "" });

  const [options, setOptions] = useState({ voltages: [], poles: [], motors_by_pole: {} });

  useEffect(() => {
    fetch(`${API_BASE}/api/options`).then(r => r.json()).then(setOptions).catch(() => {});
  }, []);

  const handleUpdate = (key, val) => {
    setFormData(prev => {
        const newData = { ...prev, [key]: val };
        
        // Sync Op Speed -> Max Speed
        if (key === "op_speed") {
            newData.max_speed = val;
        }

        // Auto-fill speed based on pole
        if (key === "pole") {
            const poleMap = { "2": "2880", "4": "1440", "6": "960", "8": "720" };
            const speed = poleMap[val] || "";
            newData.op_speed = speed;
            newData.max_speed = speed;
        }

        return newData;
    });
  };

  const sanitizeFilenamePart = (value) => {
    if (!value) return "";
    const trimmed = String(value).trim();
    return trimmed
      .replace(/[\\/:*?"<>|]+/g, "")
      .replace(/\s+/g, " ")
      .trim();
  };

  const generateTestSheet = async () => {
    const serialRaw = formData.serial_no || "";
    const customerRaw = formData.customer_name || "";
    if (!customerRaw.trim()) {
      setErrors((prev) => ({ ...prev, customer_name: "Customer Name is required" }));
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/reports/test-record-sheet/from-nameplate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!response.ok) throw new Error("Failed to generate Test Sheet");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const serialPart = sanitizeFilenamePart(serialRaw) || "UNKNOWN";
      a.download = `Test Sheet${serialPart}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      console.error(e);
      alert("Failed to generate Test Sheet. Please try again.");
    }
  };

  const generatePDF = async () => {
    const customerRaw = formData.customer_name || "";
    if (!customerRaw.trim()) {
      setErrors((prev) => ({ ...prev, customer_name: "Customer Name is required" }));
      return;
    }

    setErrors((prev) => ({ ...prev, customer_name: "" }));

    try {
      const response = await fetch(`${API_BASE}/api/generate-pdf`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Failed to generate PDF");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const customerPart = sanitizeFilenamePart(formData.customer_name) || "Nameplate";
      const serialPart = sanitizeFilenamePart(formData.serial_no) || "preview";
      const fileName = `${customerPart}-${serialPart}.pdf`;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      console.error("Error generating PDF:", error);
      alert("Failed to generate PDF. Please try again.");
    }
  };

  const { motor, pole, voltage } = formData;

  // Auto-calculate FLA and Connection
  useEffect(() => {
    if (motor && pole && voltage) {
        // Fetch FLA
        fetch(`${API_BASE}/api/fla?motor=${encodeURIComponent(motor)}&pole=${encodeURIComponent(pole)}&voltage=${encodeURIComponent(voltage)}`)
            .then(r => r.json())
            .then(data => {
                setFormData(prev => ({ ...prev, fla: data.fla || "" }));
            })
            .catch(console.error);

        // Fetch Connection
        fetch(`${API_BASE}/api/connection?motor=${encodeURIComponent(motor)}&pole=${encodeURIComponent(pole)}&voltage=${encodeURIComponent(voltage)}`)
            .then(r => r.json())
            .then(data => {
                setFormData(prev => ({ ...prev, connection: data.connection || "" }));
            })
            .catch(console.error);
    }
  }, [motor, pole, voltage]);

  return (
    <div className="page-container">
      <div className="layout-grid">
        <div className="form-card">
          <div className="form-header">
            <div className="header-accent"></div>
            <h2 className="header-title">Nameplate Configuration</h2>
          </div>

          <div className="form-grid">
            <div className="field-container" style={{ gridColumn: "1 / -1" }}>
              <label className="field-label">Customer Name</label>
              <input
                className={`field-input${errors.customer_name ? " field-input-error" : ""}`}
                value={formData.customer_name}
                onChange={(e) => {
                  const value = e.target.value;
                  handleUpdate("customer_name", value);
                  if (value.trim()) {
                    setErrors((prev) => ({ ...prev, customer_name: "" }));
                  }
                }}
                placeholder="Enter customer name"
              />
              <div style={{ fontSize: 11, color: "#4b5563", marginTop: 4 }}>
                Used for the PDF document title and downloaded file name
              </div>
              {errors.customer_name && (
                <div className="field-error">{errors.customer_name}</div>
              )}
            </div>

            <div className="section-header">🛠 Identification</div>
            <Field label="Serial No." value={formData.serial_no} onChange={(v) => handleUpdate("serial_no", v)} placeholder="e.g. FM12345" />
            <Field label="Series" value={formData.series} onChange={(v) => handleUpdate("series", v)} placeholder="e.g. MAXFLO" />
            <Field label="Size" value={formData.size} onChange={(v) => handleUpdate("size", v)} placeholder="e.g. 630/165" />
            <Field label="Class / Pitch" value={formData.class_pitch} onChange={(v) => handleUpdate("class_pitch", v)} placeholder="e.g. 34" />
            <div className="field-container">
              <label className="field-label">Manufacturer</label>
              <input className="field-input" value={formData.manufacturer} onChange={(e) => handleUpdate("manufacturer", e.target.value)} placeholder="e.g. ACTION" />
            </div>
            <div className="field-container">
              <label className="field-label">Date of Manuf</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                <select className="field-select" value={(formData.date_of_manuf.split(" ")[0] || "").toUpperCase()} onChange={(e) => {
                  const month = e.target.value;
                  const year = (formData.date_of_manuf.split(" ")[1] || "").toUpperCase();
                  handleUpdate("date_of_manuf", `${month} ${year}`.trim());
                }}>
                  <option value="">Month</option>
                  {["JAN.", "FEB.", "MAR.", "APR.", "MAY", "JUN.", "JUL.", "AUG.", "SEP.", "OCT.", "NOV.", "DEC."].map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                <select className="field-select" value={(formData.date_of_manuf.split(" ")[1] || "")} onChange={(e) => {
                  const year = e.target.value;
                  const month = (formData.date_of_manuf.split(" ")[0] || "").toUpperCase();
                  handleUpdate("date_of_manuf", `${month} ${year}`.trim());
                }}>
                  <option value="">Year</option>
                  {Array.from({ length: 50 }, (_, i) => 1986 + i).map(y => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="section-header">⚡ Electrical Specs</div>
            <div className="field-container">
              <label className="field-label">POLES</label>
              <select
                className="field-select"
                value={formData.pole}
                onChange={(e) => handleUpdate("pole", e.target.value)}
              >
                <option value="">Select...</option>
                {options.poles.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <div className="field-container">
              <label className="field-label">MOTOR (kW)</label>
              <select
                className="field-select"
                value={formData.motor}
                onChange={(e) => handleUpdate("motor", e.target.value)}
              >
                <option value="">Select...</option>
                {(options.motors_by_pole[formData.pole] || []).map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>

            <div className="field-container">
              <label className="field-label">Voltage</label>
              <select className="field-select" value={formData.voltage} onChange={(e) => handleUpdate("voltage", e.target.value)}>
                <option value="">Select...</option>
                {options.voltages.map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
            <Field label="Phase" value={formData.phase} disabled />
            <Field label="Frequency" value={formData.frequency} onChange={(v) => handleUpdate("frequency", v)} />
            <Field label="FLA (Auto)" value={formData.fla} disabled placeholder="Calculated..." />
            <Field label="Connection" value={formData.connection} disabled placeholder="Calculated..." />
            
            <div className="section-header">⚙ Operational</div>
            <Field label="Op Speed" value={formData.op_speed} onChange={(v) => handleUpdate("op_speed", v)} placeholder="RPM" />
            <Field label="Max Speed" value={formData.max_speed} onChange={(v) => handleUpdate("max_speed", v)} placeholder="RPM" />
            <Field label="Op Temp" value={formData.op_temp} onChange={(v) => handleUpdate("op_temp", v)} placeholder="°C" />
            <Field label="Relube Interval" value={formData.relube_interval} onChange={(v) => handleUpdate("relube_interval", v)} placeholder="Hours or N/A" />
            
            <div style={{ gridColumn: "1 / -1", marginTop: "20px" }}>
              <button
                onClick={generatePDF}
                className="btn-primary"
              >
                Download PDF
              </button>
              <div style={{ height: 8 }} />
              <button onClick={generateTestSheet} className="btn-primary">Generate Test Sheet</button>
            </div>
          </div>
        </div>

        <div className="preview-sticky">
          <div className="preview-wrapper">
            <LivePreview formData={formData} />
          </div>
        </div>
      </div>
    </div>
  );
}
