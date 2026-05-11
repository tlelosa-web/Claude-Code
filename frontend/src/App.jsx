import { useState } from "react";
import FormFields from "./components/FormFields";

function App() {
  const [formData, setFormData] = useState({
    customer_name: "",
    serial_no: "",
    series: "",
    size: "",
    motor: "",
    pole: "",
    voltage: "",
  });

  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("");

  // =========================
  // CENTRAL VALIDATION (AUTHORITATIVE)
  // =========================
  const validateForm = (data) => {
    const errs = {};

    if (!data.customer_name?.trim())
      errs.customer_name = "Customer Name is required";

    if (!data.serial_no?.trim())
      errs.serial_no = "Serial No. is required";

    if (!data.series?.trim())
      errs.series = "Series is required";

    if (!data.size?.trim())
      errs.size = "Size is required";

    if (!data.motor || !data.pole || !data.voltage) {
      errs.electrical =
        "Motor kW, Pole count, and Voltage are all required";
    }

    return errs;
  };

  // =========================
  // HANDLERS
  // =========================
  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const generateNameplatePDF = async () => {
    const errs = validateForm(formData);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setErrors({});
    setStatus("Generating Nameplate PDF...");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/generate-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to generate Nameplate PDF");
      }

      setStatus("Nameplate PDF generated successfully");
    } catch (err) {
      setStatus(err.message);
    }
  };

  const generateTestSheetPDF = async () => {
    const errs = validateForm(formData);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setErrors({});
    setStatus("Generating Test Record Sheet...");

    try {
      const res = await fetch(
        "http://127.0.0.1:8000/api/reports/test-record-sheet/from-nameplate",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData),
        }
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to generate Test Record Sheet");
      }

      setStatus("Test Record Sheet generated successfully");
    } catch (err) {
      setStatus(err.message);
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Nameplate Entry</h2>

      <FormFields
        data={formData}
        errors={errors}
        onChange={handleChange}
      />

      {errors.electrical && (
        <div style={{ color: "red", marginTop: "10px" }}>
          {errors.electrical}
        </div>
      )}

      <div style={{ marginTop: "20px" }}>
        <button onClick={generateNameplatePDF}>
          Generate Nameplate PDF
        </button>

        <button
          onClick={generateTestSheetPDF}
          style={{ marginLeft: "10px" }}
        >
          Generate Test Record Sheet
        </button>
      </div>

      {status && (
        <div style={{ marginTop: "20px" }}>
          <strong>Status:</strong> {status}
        </div>
      )}
    </div>
  );
}

export default App;
