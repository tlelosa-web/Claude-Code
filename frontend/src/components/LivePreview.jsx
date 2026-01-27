import React from "react";

// Physical dimensions in mm (from pdf_generator.py)
const PLATE_W_MM = 105.0;
const PLATE_H_MM = 104.0;
const BORDER_MARGIN_MM = 4.0;
const BOX_H_MM = 5.5;

// Scale factor: 1mm = 6px (Slightly larger for better visibility)
const SCALE = 6;

// Helper for converting mm to px string
const mm = (val) => `${val * SCALE}px`;

// Font sizes (converted from pt to mm approx: 1pt ~ 0.35mm)
const fonts = {
  headerMain: mm(18 * 0.35),    // 18pt
  headerSub: mm(12 * 0.35),     // 12pt
  headerTag: mm(8 * 0.35),      // 8pt
  sectionTitle: mm(12 * 0.35),  // 12pt
  label: mm(8 * 0.35),          // 8pt
  value: mm(8 * 0.35),          // 8pt
  unit: mm(7 * 0.35),           // 7pt
  footer: mm(8 * 0.35),         // 8pt
  footerSmall: mm(7 * 0.35)     // 7pt
};

// Colors
const COLORS = {
  bg: "#1a3b8e",      // Deep industrial blue
  border: "#d1d5db",  // Silver/White border
  boxFill: "#e5e7eb", // Light grey
  text: "#000000",    // Black text inside boxes
  label: "#ffffff",   // White text on blue background
  screw: "#374151"    // Dark grey for screws
};

// X Coordinates (from pdf_generator.py)
const X = {
  series: 17.0,
  seriesW: 35.0,
  
  leftStd: 17.0,
  leftStdW: 29.0,
  
  leftSmall: 20.0,
  leftSmallW: 24.0,
  
  size: 63.0,
  sizeW: 36.5,
  
  rightStd: 70.5,
  rightStdW: 20.5,
  
  relube: 38.0,
  relubeW: 29.0,
  
  leftLabel: 5.0,  // BORDER_MARGIN_MM + 1.0
  rightLabel: 54.0
};

// Row Top Y calculation (CSS Top)
// PDF: ROW0_BOX_TOP_Y_MM = 104 - 34 = 70
// CSS Top = 34
const ROW0_TOP = 34.0;
const ROW_PITCH = 6.5;
const rowTop = (i) => ROW0_TOP + (i * ROW_PITCH);

// Components
const AbsoluteBox = ({ x, y, w, h, value, fontSize }) => (
  <div style={{
    position: "absolute",
    left: mm(x),
    top: mm(y),
    width: mm(w),
    height: mm(h),
    background: COLORS.boxFill,
    border: "1px solid black",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: COLORS.text,
    fontSize: fontSize || fonts.value,
    fontFamily: "Helvetica, Arial, sans-serif",
    whiteSpace: "nowrap",
    overflow: "hidden"
  }}>
    {value}
  </div>
);

const AbsoluteLabel = ({ x, y, text, width, align = "left", size = fonts.label, bold = true }) => (
  <div style={{
    position: "absolute",
    left: mm(x),
    top: mm(y), // This should be centered relative to the box
    width: width ? mm(width) : "auto",
    color: COLORS.label,
    fontSize: size,
    fontFamily: "Helvetica, Arial, sans-serif",
    fontWeight: bold ? "bold" : "normal",
    textAlign: align,
    whiteSpace: "pre" // Respect newlines
  }}>
    {text}
  </div>
);

const UnitLabel = ({ x, y, text }) => (
  <div style={{
    position: "absolute",
    left: mm(x),
    top: mm(y),
    color: COLORS.label,
    fontSize: fonts.unit,
    fontWeight: "bold",
    fontFamily: "Helvetica, Arial, sans-serif"
  }}>
    {text}
  </div>
);

// Screw Helper
const Screw = ({ x, y }) => (
  <div style={{
    position: "absolute",
    left: mm(x),
    top: mm(y),
    width: mm(3),
    height: mm(3),
    borderRadius: "50%",
    background: "radial-gradient(circle at 30% 30%, #9ca3af, #374151)",
    border: "1px solid #4b5563",
    boxShadow: "1px 1px 2px rgba(0,0,0,0.5)"
  }} />
);

export default function LivePreview({ formData }) {
  // Box vertical offset for labels (centering text vertically relative to 5.5mm box)
  // Box is 5.5mm high. Text is ~2.8mm high.
  // Top padding approx 1.35mm.
  const labelOffsetY = 1.2; 
  const unitOffsetY = 1.5;

  return (
    <div style={{
      width: mm(PLATE_W_MM),
      height: mm(PLATE_H_MM),
      background: COLORS.bg,
      border: `4px solid ${COLORS.border}`,
      borderRadius: "12px", // Slight radius for look
      position: "relative",
      boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
      fontFamily: "Helvetica, Arial, sans-serif",
      boxSizing: "border-box", // Important so border is inside width/height if set, but here we set content size... wait. 
      // Actually standard box-model: width + border. 
      // If we want exact match, the container content should be PLATE_W_MM.
      // With box-sizing: border-box, padding/border reduces content.
      // Let's use content-box and subtract border? Or just let it be slightly larger outer.
      // For precision, let's assume the div IS the plate.
    }}>
      {/* Inner Border Line (White/Silver line inside) */}
      <div style={{
        position: "absolute",
        left: mm(BORDER_MARGIN_MM),
        top: mm(BORDER_MARGIN_MM),
        width: mm(PLATE_W_MM - 2 * BORDER_MARGIN_MM),
        height: mm(PLATE_H_MM - 2 * BORDER_MARGIN_MM),
        border: "2px solid #d1d5db",
        pointerEvents: "none"
      }} />

      {/* Screws */}
      <Screw x={1.5} y={1.5} />
      <Screw x={PLATE_W_MM - 4.5} y={1.5} />
      <Screw x={1.5} y={PLATE_H_MM - 4.5} />
      <Screw x={PLATE_W_MM - 4.5} y={PLATE_H_MM - 4.5} />

      {/* Header */}
      <div style={{ position: "absolute", width: "100%", top: mm(10 - 5), textAlign: "center" }}>
        <div style={{ fontSize: fonts.headerMain, fontWeight: "bold", color: COLORS.label }}>FAN</div>
      </div>
      <div style={{ position: "absolute", width: "100%", top: mm(17 - 3.5), textAlign: "center" }}>
        <div style={{ fontSize: fonts.headerSub, fontWeight: "bold", color: COLORS.label }}>MOVEMENT</div>
      </div>
      <div style={{ position: "absolute", width: "100%", top: mm(22 - 2), textAlign: "center" }}>
        <div style={{ fontSize: fonts.headerTag, fontWeight: "bold", color: COLORS.label }}>AIR AND GAS MOVEMENT SOLUTIONS</div>
      </div>

      <AbsoluteLabel x={X.leftLabel} y={27} text="FAN DATA" size={fonts.sectionTitle} />

      {/* Row 0 */}
      <AbsoluteLabel x={X.leftLabel} y={rowTop(0) + labelOffsetY} text="Series:" />
      <AbsoluteBox x={X.series} y={rowTop(0)} w={X.seriesW} h={BOX_H_MM} value={formData.series} />
      
      <AbsoluteLabel x={X.rightLabel} y={rowTop(0) + labelOffsetY} text="Size:" />
      <AbsoluteBox x={X.size} y={rowTop(0)} w={X.sizeW} h={BOX_H_MM} value={formData.size} />

      {/* Row 1 */}
      <AbsoluteLabel x={X.leftLabel} y={rowTop(1) + labelOffsetY - 0.4} text={"Class /\nPitch:"} size={fonts.unit} />
      <AbsoluteBox x={X.leftStd} y={rowTop(1)} w={X.leftStdW} h={BOX_H_MM} value={formData.class_pitch} />

      <AbsoluteLabel x={X.rightLabel} y={rowTop(1) + labelOffsetY} text="Op. Speed:" />
      <AbsoluteBox x={X.rightStd} y={rowTop(1)} w={X.rightStdW} h={BOX_H_MM} value={formData.op_speed} />
      <UnitLabel x={X.rightStd + X.rightStdW + 1} y={rowTop(1) + unitOffsetY} text="RPM" />

      {/* Row 2 */}
      <AbsoluteLabel x={X.leftLabel} y={rowTop(2) + labelOffsetY} text="Motor:" />
      <AbsoluteBox x={X.leftStd} y={rowTop(2)} w={X.leftStdW} h={BOX_H_MM} value={formData.motor} />
      <UnitLabel x={X.leftStd + X.leftStdW + 1} y={rowTop(2) + unitOffsetY} text="kW" />

      <AbsoluteLabel x={X.rightLabel} y={rowTop(2) + labelOffsetY} text="Max Speed:" />
      <AbsoluteBox x={X.rightStd} y={rowTop(2)} w={X.rightStdW} h={BOX_H_MM} value={formData.max_speed} />
      <UnitLabel x={X.rightStd + X.rightStdW + 1} y={rowTop(2) + unitOffsetY} text="RPM" />

      {/* Row 3 */}
      <AbsoluteLabel x={X.leftLabel} y={rowTop(3) + labelOffsetY} text="Voltage:" />
      <AbsoluteBox x={X.leftStd} y={rowTop(3)} w={X.leftStdW} h={BOX_H_MM} value={formData.voltage} />
      <UnitLabel x={X.leftStd + X.leftStdW + 1} y={rowTop(3) + unitOffsetY} text="V" />

      <AbsoluteLabel x={X.rightLabel} y={rowTop(3) + labelOffsetY} text="Phase:" />
      <AbsoluteBox x={X.rightStd} y={rowTop(3)} w={X.rightStdW} h={BOX_H_MM} value={formData.phase} />

      {/* Row 4 */}
      <AbsoluteLabel x={X.leftLabel} y={rowTop(4) + labelOffsetY} text="F.L.A:" />
      <AbsoluteBox x={X.leftStd} y={rowTop(4)} w={X.leftStdW} h={BOX_H_MM} value={formData.fla} />

      <AbsoluteLabel x={X.rightLabel} y={rowTop(4) + labelOffsetY} text="Frequency:" />
      <AbsoluteBox x={X.rightStd} y={rowTop(4)} w={X.rightStdW} h={BOX_H_MM} value={formData.frequency} />
      <UnitLabel x={X.rightStd + X.rightStdW + 1} y={rowTop(4) + unitOffsetY} text="Hz" />

      {/* Row 5 */}
      <AbsoluteLabel x={X.leftLabel} y={rowTop(5) + labelOffsetY} text="Op Temp:" />
      <AbsoluteBox x={X.leftSmall} y={rowTop(5)} w={X.leftSmallW} h={BOX_H_MM} value={formData.op_temp} />
      <UnitLabel x={X.leftSmall + X.leftSmallW + 1} y={rowTop(5) + unitOffsetY} text="°C" />

      <AbsoluteLabel x={X.rightLabel} y={rowTop(5) + labelOffsetY} text="Conn:" />
      <AbsoluteBox x={X.rightStd} y={rowTop(5)} w={X.rightStdW} h={BOX_H_MM} value={formData.connection} />

      {/* Row 6 */}
      <AbsoluteLabel x={X.leftLabel} y={rowTop(6) + labelOffsetY} text="Serial No:" />
      <AbsoluteBox x={X.leftSmall} y={rowTop(6)} w={X.leftSmallW} h={BOX_H_MM} value={formData.serial_no} />

      <AbsoluteLabel x={X.rightLabel} y={rowTop(6)} text="Date of" size={fonts.unit} />
      <AbsoluteLabel x={X.rightLabel} y={rowTop(6) + 2.5} text="Manuf.:" size={fonts.unit} />
      <AbsoluteBox x={X.rightStd} y={rowTop(6)} w={X.rightStdW} h={BOX_H_MM} value={formData.date_of_manuf} />

      {/* Relube */}
      {/* PDF: relube_box_top = 18.5 (from bottom?) No, 18.5 is Y coord from bottom. */}
      {/* Wait, my CSS Top calculation was: 104 - 18.5 = 85.5 */}
      <AbsoluteLabel x={X.leftLabel} y={85.5 + labelOffsetY} text="Re-Lubrication Interval:" size={fonts.unit} />
      <AbsoluteBox x={X.relube} y={85.5} w={X.relubeW} h={BOX_H_MM} value={formData.relube_interval} />

      {/* Footer */}
      <div style={{ position: "absolute", width: "100%", top: mm(93), textAlign: "center" }}>
        <div style={{ fontSize: fonts.footer, fontWeight: "bold", color: COLORS.label }}>FAN MOVEMENT 011 682 3020</div>
      </div>
      <div style={{ position: "absolute", width: "100%", top: mm(96), textAlign: "center" }}>
        <div style={{ fontSize: fonts.footerSmall, color: COLORS.label }}>www.fanmovement.co.za</div>
      </div>
      <div style={{ position: "absolute", width: "100%", top: mm(98.5), textAlign: "center" }}>
        <div style={{ fontSize: fonts.footerSmall, color: COLORS.label }}>info@fanmovement.co.za</div>
      </div>

    </div>
  );
}
