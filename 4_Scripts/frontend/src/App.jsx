import { useEffect, useMemo, useRef, useState } from "react";
import FormFields from "./components/FormFields";
import LivePreview from "./components/LivePreview";
import "./App.css";

const getLocalIsoDate = () => {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
};

function App() {
  const apiBase = useMemo(() => (import.meta.env.VITE_API_BASE || "").replace(/\/$/, ""), []);
  const touchedRef = useRef(new Set());
  const autoTimerRef = useRef(null);
  const previewTimerRef = useRef(null);
  const previewDataKeyRef = useRef("");

  const [formData, setFormData] = useState({
    customer_name: "",
    serial_no: "",
    series: "",
    class_pitch: "",
    imp_form: "FORM B",
    size: "",
    motor: "",
    pole: "",
    voltage: "",
    phase: "",
    date_of_manuf: getLocalIsoDate(),
    quantity: "1",
    frequency: "50",
    op_temp: "20",
    op_speed: "",
    fla: "",
    connection: "",
    relube_interval: "N/A",
    manufacturer: "",
  });

  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("");
  const [options, setOptions] = useState({});
  const [busyState, setBusyState] = useState({
    saving: false,
    loadingExcel: false,
    preview: false,
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [testSheetPreviewUrl, setTestSheetPreviewUrl] = useState("");

  const busy = busyState.saving || busyState.loadingExcel || busyState.preview;

  const buildRequestPayload = () => ({
    ...formData,
    quantity: parseInt(formData.quantity, 10) || 1,
  });

  const getPreviewDataKey = (data) =>
    JSON.stringify({
      customer_name: data.customer_name,
      serial_no: data.serial_no,
      series: data.series,
      class_pitch: data.class_pitch,
      imp_form: data.imp_form,
      size: data.size,
      motor: data.motor,
      pole: data.pole,
      voltage: data.voltage,
      phase: data.phase,
      date_of_manuf: data.date_of_manuf,
      quantity: data.quantity,
      frequency: data.frequency,
      op_temp: data.op_temp,
      op_speed: data.op_speed,
      fla: data.fla,
      connection: data.connection,
      relube_interval: data.relube_interval,
      manufacturer: data.manufacturer,
    });

  useEffect(() => {
    return () => {
      if (testSheetPreviewUrl) URL.revokeObjectURL(testSheetPreviewUrl);
    };
  }, [testSheetPreviewUrl]);

  useEffect(() => {
    let cancelled = false;
    const loadOptions = async () => {
      try {
        const res = await fetch(`${apiBase}/api/options`);
        const data = await res.json();
        if (!cancelled) setOptions(data);
      } catch {
        if (!cancelled) setOptions({});
      }
    };
    loadOptions();
    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  useEffect(() => {
    const pole = String(formData.pole || "").trim();
    const motor = String(formData.motor || "").trim();
    const voltage = String(formData.voltage || "").trim();

    if (autoTimerRef.current) clearTimeout(autoTimerRef.current);
    autoTimerRef.current = setTimeout(async () => {
      if (pole && !touchedRef.current.has("op_speed")) {
        const map = { "2": "2880", "4": "1440", "6": "960", "8": "720" };
        const sp = map[pole] || "";
        if (sp) {
          setFormData((prev) => ({ ...prev, op_speed: sp }));
        }
      }

      if (!motor || !pole || !voltage) return;

      try {
        if (!touchedRef.current.has("fla")) {
          const flaRes = await fetch(`${apiBase}/api/fla?motor=${encodeURIComponent(motor)}&pole=${encodeURIComponent(pole)}&voltage=${encodeURIComponent(voltage)}`);
          const flaData = await _readJsonSafely(flaRes);
          if (flaRes.ok && flaData?.fla) {
            setFormData((prev) => ({ ...prev, fla: String(flaData.fla) }));
          }
        }
      } catch {
        // Auto-fill is opportunistic; manual form values remain authoritative.
      }

      try {
        if (!touchedRef.current.has("connection")) {
          const cRes = await fetch(`${apiBase}/api/connection?motor=${encodeURIComponent(motor)}&pole=${encodeURIComponent(pole)}&voltage=${encodeURIComponent(voltage)}`);
          const cData = await _readJsonSafely(cRes);
          if (cRes.ok && cData?.connection) {
            setFormData((prev) => ({ ...prev, connection: prev.connection || String(cData.connection) }));
          }
        }
      } catch {
        // Auto-fill is opportunistic; manual form values remain authoritative.
      }
    }, 250);

    return () => {
      if (autoTimerRef.current) clearTimeout(autoTimerRef.current);
    };
  }, [apiBase, formData.motor, formData.pole, formData.voltage, formData.op_speed, formData.fla, formData.connection]);

  useEffect(() => {
    if (previewTimerRef.current) clearTimeout(previewTimerRef.current);

    // Don't block preview on validation errors - just skip auto-refresh
    const errs = validateForm(formData);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      // Clear preview if validation fails
      if (testSheetPreviewUrl) {
        URL.revokeObjectURL(testSheetPreviewUrl);
        setTestSheetPreviewUrl("");
      }
      return;
    }
    if (busyState.saving || busyState.loadingExcel) return;

    const nextPreviewDataKey = getPreviewDataKey(formData);
    if (nextPreviewDataKey === previewDataKeyRef.current) return;

    previewTimerRef.current = setTimeout(() => {
      refreshTestSheetPreview({ silent: true });
    }, 600);

    return () => {
      if (previewTimerRef.current) clearTimeout(previewTimerRef.current);
    };
  }, [
    busy,
    formData.customer_name,
    formData.serial_no,
    formData.series,
    formData.size,
    formData.motor,
    formData.pole,
    formData.voltage,
    formData.class_pitch,
    formData.imp_form,
    formData.phase,
    formData.date_of_manuf,
    formData.quantity,
    formData.frequency,
    formData.op_temp,
    formData.op_speed,
    formData.fla,
    formData.connection,
    formData.relube_interval,
    formData.manufacturer,
  ]);

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

    const qty = parseInt(data.quantity, 10);
    if (!qty || qty < 1) errs.quantity = "Quantity must be at least 1.";
    else if (qty > 20) errs.quantity = "Quantity cannot exceed 20 (test sheet capacity).";

    return errs;
  };

  // =========================
  // HANDLERS
  // =========================
  const handleChange = (field, value) => {
    touchedRef.current.add(field);
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const _errMsg = (err) => {
    if (!err) return "Unknown error";
    if (typeof err === "string") return err;
    if (typeof err?.message === "string") return err.message;
    return String(err);
  };

  const _downloadPdfResponse = async (res, fallbackFileName) => {
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    try {
      const a = document.createElement("a");
      a.href = url;
      a.download = fallbackFileName;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } finally {
      URL.revokeObjectURL(url);
    }
  };

  const _readJsonSafely = async (res) => {
    try {
      return await res.json();
    } catch {
      return null;
    }
  };

  const requestPdf = async (path, payload, fallbackFileName) => {
    setBusyState((prev) => ({ ...prev, saving: true }));
    try {
      const res = await fetch(`${apiBase}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await _readJsonSafely(res);
        throw new Error(err?.error || err?.detail || "Request failed");
      }

      await _downloadPdfResponse(res, fallbackFileName);
    } finally {
      setBusyState((prev) => ({ ...prev, saving: false }));
    }
  };

  const refreshTestSheetPreview = async ({ silent } = { silent: false }) => {
    const errs = validateForm(formData);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    if (!silent) setStatus("Refreshing Test Sheet preview...");

    // Update the ref immediately to prevent infinite retry loops if the fetch fails
    previewDataKeyRef.current = getPreviewDataKey(formData);

    setBusyState((prev) => ({ ...prev, preview: true }));
    try {
      const res = await fetch(`${apiBase}/api/reports/test-record-sheet/from-nameplate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildRequestPayload()),
      });

      if (!res.ok) {
        const err = await _readJsonSafely(res);
        throw new Error(err?.error || err?.detail || "Failed to generate Test Sheet preview");
      }

      const blob = await res.blob();
      const url = `${URL.createObjectURL(blob)}#view=FitH`;
      setTestSheetPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return url;
      });
      if (!silent) setStatus("Test Sheet preview updated");
    } catch (err) {
      if (!silent) setStatus(_errMsg(err));
    } finally {
      setBusyState((prev) => ({ ...prev, preview: false }));
    }
  };

  const loadFromExcel = async () => {
    setStatus("Loading from Excel...");
    try {
      setBusyState((prev) => ({ ...prev, loadingExcel: true }));
      const res = await fetch(`${apiBase}/api/nameplate/from-excel`);
      const data = await _readJsonSafely(res);
      if (!res.ok) {
        throw new Error(data?.error || data?.detail || "Failed to load from Excel");
      }
      const np = data?.nameplate || {};
      touchedRef.current = new Set();
      setFormData((prev) => ({
        ...prev,
        report_date: np.report_date ?? prev.report_date,
        customer_name: np.customer_name ?? prev.customer_name,
        serial_no: np.serial_no ?? prev.serial_no,
        series: np.series ?? prev.series,
        class_pitch: np.class_pitch ?? prev.class_pitch,
        imp_form: np.imp_form ?? prev.imp_form,
        size: np.size ?? prev.size,
        motor: np.motor ?? prev.motor,
        pole: np.pole ?? prev.pole,
        voltage: np.voltage ?? prev.voltage,
        phase: np.phase ?? prev.phase,
        date_of_manuf: np.date_of_manuf ?? prev.date_of_manuf,
        op_speed: np.op_speed ?? prev.op_speed,
        fla: np.fla ?? prev.fla,
        connection: np.connection ?? prev.connection,
        frequency: np.frequency ?? prev.frequency,
        op_temp: np.op_temp ?? prev.op_temp,
        relube_interval: np.relube_interval ?? prev.relube_interval,
        manufacturer: np.manufacturer ?? prev.manufacturer,
      }));
      setStatus("Loaded values from Excel");
    } catch (err) {
      setStatus(_errMsg(err));
    } finally {
      setBusyState((prev) => ({ ...prev, loadingExcel: false }));
    }
  };

  const generateNameplatePDF = async () => {
    const errs = validateForm(formData);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      setStatus("Please fix form errors before saving.");
      return;
    }

    setErrors({});
    setStatus("Generating Nameplate PDF...");

    try {
      const serialSafe = (formData.serial_no || "UNKNOWN").trim() || "UNKNOWN";
      await requestPdf("/api/generate-pdf", formData, `Nameplate_${serialSafe}.pdf`);
      setStatus("Nameplate PDF generated and downloaded");
    } catch (err) {
      setStatus(_errMsg(err));
    }
  };

  const generateTestSheetPDF = async () => {
    const errs = validateForm(formData);
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      setStatus("Please fix form errors before saving.");
      return;
    }

    setErrors({});
    setStatus("Generating Test Record Sheet...");

    try {
      const serialSafe = (formData.serial_no || "UNKNOWN").trim() || "UNKNOWN";
      await requestPdf(
        "/api/reports/test-record-sheet/from-nameplate",
        buildRequestPayload(),
        `TestSheet_${serialSafe}.pdf`
      );
      setStatus("Test Record Sheet generated and downloaded");
    } catch (err) {
      setStatus(_errMsg(err));
    }
  };

  const resetForm = () => {
    touchedRef.current = new Set();
    setErrors({});
    setStatus("");
    setFormData({
      report_date: getLocalIsoDate(),
      customer_name: "",
      serial_no: "",
      series: "",
      class_pitch: "",
      imp_form: "FORM B",
      size: "",
      motor: "",
      pole: "",
      voltage: "",
      phase: "",
      date_of_manuf: "",
      quantity: "1",
      frequency: "50",
      op_temp: "20",
      op_speed: "",
      fla: "",
      connection: "",
      relube_interval: "N/A",
      manufacturer: "",
    });
    if (testSheetPreviewUrl) URL.revokeObjectURL(testSheetPreviewUrl);
    setTestSheetPreviewUrl("");
  };

  return (
    <div className="app-shell">
      <div className="main">
        <header className="topbar">
          <div className="brand">
            <span className="brand-badge" />
            NAMEPLATE TOOL
          </div>
            <div className="status-pill">
              <span className={`dot${busy ? " dot-busy" : ""}`} />
              {busy ? "Busy" : "Ready"}
            </div>
        </header>

        <main className="content">

          <div className="dashboard">
            <div className="grid-with-preview">
              <div className="card main-form-card">
                <div className="card-header">
                  <h2 className="card-title">Add a new nameplate</h2>
                  <div className="card-actions">
                    <button className="btn btn-primary" type="button" onClick={() => setShowAdvanced((v) => !v)}>
                      {showAdvanced ? "Hide Fields" : "Edit Fields"}
                    </button>
                    <button className="btn" type="button" onClick={() => refreshTestSheetPreview()} disabled={busyState.preview}>
                      Refresh Preview
                    </button>
                  </div>
                </div>
                <div className="card-body">
                  <FormFields
                    data={formData}
                    errors={errors}
                    onChange={handleChange}
                    options={options}
                    showAdvanced={showAdvanced}
                  />
                </div>
                <div className="footer-actions">
                  <button className="btn btn-primary" type="button" onClick={generateNameplatePDF} disabled={busyState.saving || busyState.loadingExcel}>
                    Save Nameplate
                  </button>
                  <button className="btn" type="button" onClick={generateTestSheetPDF} disabled={busyState.saving || busyState.loadingExcel}>
                    Save Test Sheet
                  </button>
                  <button className="btn" type="button" onClick={resetForm} disabled={busyState.saving || busyState.loadingExcel}>
                    Close
                  </button>
                </div>
              </div>

              <div className="card preview-card">
                <div className="preview-title">
                  <span>Nameplate Preview</span>
                  <span style={{ fontSize: 12, color: "#6b7280" }}>Live</span>
                </div>
                <div className="preview-body">
                  <LivePreview formData={formData} />
                </div>
              </div>

              <div className="card preview-card">
                <div className="preview-title">
                  <span>Test Sheet Preview</span>
                  <button className="btn" type="button" onClick={() => refreshTestSheetPreview()} disabled={busyState.preview}>
                    Refresh
                  </button>
                </div>
                <div className="preview-body" style={{ padding: 0 }}>
                  {testSheetPreviewUrl ? (
                    <iframe className="pdf-frame" src={testSheetPreviewUrl} title="Test Sheet Preview" />
                  ) : (
                    <div style={{ padding: 12, fontSize: 13, color: "#6b7280" }}>
                      Enter required fields, then click Refresh.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {status ? (
            <div style={{ marginTop: 12, fontSize: 13, color: "#374151" }}>
              <strong>Status:</strong> {status}
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}

export default App;
