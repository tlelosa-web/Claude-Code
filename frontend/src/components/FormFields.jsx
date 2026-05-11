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

export default function FormFields({ data, errors, onChange, options = {} }) {
  const volts = options.voltages || [];
  const poles = options.poles || [];
  const motorsByPole = options.motors_by_pole || {};
  const motorOptions = motorsByPole[data.pole] || [];
  return (
    <div>
      <SectionHeader title="Customer" />
      <Field label="Customer Name" value={data.customer_name} onChange={(v) => onChange("customer_name", v)} placeholder="e.g. ACME Ltd" />
      <Field label="Serial No." value={data.serial_no} onChange={(v) => onChange("serial_no", v)} placeholder="e.g. FM5107" />
      <SectionHeader title="Fan" />
      <Field label="Series" value={data.series} onChange={(v) => onChange("series", v)} />
      <Field label="Size" value={data.size} onChange={(v) => onChange("size", v)} />
      <SectionHeader title="Electrical" />
      <Select label="Voltage" value={data.voltage} onChange={(v) => onChange("voltage", v)} options={volts} />
      <Select label="Poles" value={data.pole} onChange={(v) => onChange("pole", v)} options={poles} />
      <Select label="Motor kW" value={data.motor} onChange={(v) => onChange("motor", v)} options={motorOptions.length ? motorOptions : []} />
    </div>
  );
}
