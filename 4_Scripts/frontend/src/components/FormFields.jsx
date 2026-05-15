import React from "react";

export function SectionHeader({ title, icon }) {
  return (
    <div className="section-header">
      {icon && <span>{icon}</span>}
      {title}
    </div>
  );
}

export function Field({ label, value, onChange, disabled, placeholder, type = "text", error, readOnly }) {
  return (
    <div className="field-container">
      <label className="field-label">{label}</label>
      <input
        className={`field-input${error ? " field-input-error" : ""}`}
        type={type}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        readOnly={readOnly}
      />
      {error ? <div className="field-error">{error}</div> : null}
    </div>
  );
}

export function Select({ label, value, onChange, options, disabled, placeholder = "Select...", error }) {
  return (
    <div className="field-container">
      <label className="field-label">{label}</label>
      <select
        className={`field-select${error ? " field-input-error" : ""}`}
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
      {error ? <div className="field-error">{error}</div> : null}
    </div>
  );
}

export default function FormFields({ data, errors, onChange, options = {}, showAdvanced }) {
  const volts = options.voltages || [];
  const poles = options.poles || [];
  const motorsByPole = options.motors_by_pole || {};
  const motorOptions = motorsByPole[data.pole] || [];
  const phaseOptions = [
    { label: "3~", value: "3~" },
    { label: "1~", value: "1~" },
    { label: "3", value: "3" },
    { label: "1", value: "1" },
  ];
  const connOptions = [
    { label: "STAR", value: "STAR" },
    { label: "DELTA", value: "DELTA" },
  ];
  const formOptions = [
    { label: "FORM A", value: "FORM A" },
    { label: "FORM B", value: "FORM B" },
    { label: "FORM C", value: "FORM C" },
  ];
  const makeOptions = [
    { label: "ACTOM", value: "ACTOM" },
    { label: "ASKARI", value: "ASKARI" },
    { label: "WEG", value: "WEG" },
  ];
  return (
    <div className="form-grid">
      <SectionHeader title="Customer" />
      <Field label="Customer Name" value={data.customer_name} onChange={(v) => onChange("customer_name", v)} placeholder="e.g. ACME Ltd" error={errors.customer_name} />
      <Field label="Serial No." value={data.serial_no} onChange={(v) => onChange("serial_no", v)} placeholder="e.g. FM5107" error={errors.serial_no} />
      <SectionHeader title="Fan" />
      <Field label="Series" value={data.series} onChange={(v) => onChange("series", v)} error={errors.series} />
      <Field label="Size" value={data.size} onChange={(v) => onChange("size", v)} error={errors.size} />
      <Field label="Class/Pitch" value={data.class_pitch} onChange={(v) => onChange("class_pitch", v)} placeholder="e.g. 26" />
      <Select label="Form" value={data.imp_form} onChange={(v) => onChange("imp_form", v)} options={formOptions} placeholder="Select form..." />
      <SectionHeader title="Motor" />
      <Select label="Make" value={data.manufacturer} onChange={(v) => onChange("manufacturer", v)} options={makeOptions} placeholder="Select make..." />
      <SectionHeader title="Electrical" />
      <Select label="Voltage" value={data.voltage} onChange={(v) => onChange("voltage", v)} options={volts} error={errors.electrical} />
      <Select label="Poles" value={data.pole} onChange={(v) => onChange("pole", v)} options={poles} error={errors.electrical} />
      <Select label="Motor kW" value={data.motor} onChange={(v) => onChange("motor", v)} options={motorOptions.length ? motorOptions : []} error={errors.electrical} />
      <Select label="Motor Phase" value={data.phase} onChange={(v) => onChange("phase", v)} options={phaseOptions} placeholder="Select..." />
      <Field label="Date of Manufacture" type="date" value={data.date_of_manuf} onChange={(v) => onChange("date_of_manuf", v)} />

      {showAdvanced ? (
        <>
          <SectionHeader title="Advanced" />
          <Field label="Frequency" value={data.frequency} onChange={(v) => onChange("frequency", v)} placeholder="e.g. 50" />
          <Field label="Op Temp" value={data.op_temp} onChange={(v) => onChange("op_temp", v)} placeholder="e.g. 20" />
        </>
      ) : null}

      <SectionHeader title="Auto-Calculated" />
      <Field label="Op Speed" value={data.op_speed} onChange={(v) => onChange("op_speed", v)} placeholder="e.g. 1440" />
      <Field label="F.L.A" value={data.fla} onChange={(v) => onChange("fla", v)} placeholder="e.g. 2.50" />
      <Select label="Connection" value={data.connection} onChange={(v) => onChange("connection", v)} options={connOptions} placeholder="Select..." />
    </div>
  );
}
