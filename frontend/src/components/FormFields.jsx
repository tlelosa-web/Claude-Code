import React from "react";

export function SectionHeader({ title, icon }) {
  return (
    <div className="section-header">
      {icon && <span>{icon}</span>}
      {title}
    </div>
  );
}

export function Field({ label, value, onChange, disabled, placeholder, type = "text" }) {
  return (
    <div className="field-container">
      <label className="field-label">{label}</label>
      <input
        className="field-input"
        type={type}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
      />
    </div>
  );
}

export function Select({ label, value, onChange, options, disabled, placeholder = "Select..." }) {
  return (
    <div className="field-container">
      <label className="field-label">{label}</label>
      <select
        className="field-select"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt.value || opt} value={opt.value || opt}>
            {opt.label || opt}
          </option>
        ))}
      </select>
    </div>
  );
}
