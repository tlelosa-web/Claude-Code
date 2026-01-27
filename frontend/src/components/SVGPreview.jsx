import React from "react";

// Plate dimensions (mm)
const PLATE_W = 105;
const PLATE_H = 104;

export default function SVGPreview({ formData }) {
  const d = formData;

  // Layout constants matching the desired design
  const borderInset = 4;
  const innerW = PLATE_W - borderInset * 2;
  const innerH = PLATE_H - borderInset * 2;

  // Field positions - adjusted for better layout
  const leftLabelX = 6;
  const leftBoxX = 17;
  const leftBoxW = 35; // Wider for series
  const leftSmallBoxX = 20;
  const leftSmallBoxW = 24; // Smaller for temp/serial
  const rightLabelX = 54;
  const rightBoxX = 70.5;
  const rightBoxW = 20.5;
  const sizeBoxX = 63;
  const sizeBoxW = 36.5;
  const relubeX = 38;
  const relubeW = 29;

  // Box dimensions
  const boxH = 5.5;
  const rowPitch = 6.5;

  // Row positions
  const firstRowTop = 34;
  const rowY = (i) => firstRowTop - (i * rowPitch);

  // Header positions - more prominent
  const titleY = borderInset + 10;
  const subtitleY = titleY + 7;
  const sloganY = subtitleY + 5;
  const fanDataY = titleY + 16;

  // Company info
  const relubeY = rowY(7);
  const companyBaseY = relubeY - boxH - 8;

  // Helper for centered text in boxes
  const boxTextProps = (x, y, w, h) => ({
    x: x + w / 2,
    y: y + h / 2,
    textAnchor: "middle",
    dominantBaseline: "central",
  });

  return (
    <div style={{ padding: "12px", background: "#fff", border: "1px solid #e5e7eb", borderRadius: "8px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", alignItems: "center" }}>
        <h3 style={{ fontSize: "14px", margin: 0, color: "#374151" }}>Live Preview</h3>
        <span style={{ fontSize: "11px", fontWeight: "bold", color: "#10b981" }}>✓ Ready</span>
      </div>

      <div style={{ display: "flex", justifyContent: "center", padding: "20px", background: "#f9fafb", borderRadius: "6px" }}>
        <svg
          viewBox={`0 0 ${PLATE_W} ${PLATE_H}`}
          style={{ width: "100%", maxWidth: "400px", height: "auto", border: "1px solid #d1d5db", borderRadius: "4px", background: "#fff" }}
        >
          {/* Border */}
          <rect
            x={borderInset}
            y={borderInset}
            width={innerW}
            height={innerH}
            fill="none"
            stroke="black"
            strokeWidth="1"
          />

          {/* Header */}
          <text x={PLATE_W / 2} y={titleY} textAnchor="middle" fontSize="8" fontWeight="bold" fill="black">
            FAN
          </text>
          <text x={PLATE_W / 2} y={subtitleY} textAnchor="middle" fontSize="6" fontWeight="bold" fill="black">
            MOVEMENT
          </text>
          <text x={PLATE_W / 2} y={sloganY} textAnchor="middle" fontSize="3.5" fill="black">
            AIR AND GAS MOVEMENT SOLUTIONS
          </text>

          {/* FAN DATA title */}
          <text x={leftLabelX} y={fanDataY} textAnchor="start" fontSize="5" fontWeight="bold" fill="black">
            FAN DATA
          </text>

          {/* Row 0: Series + Size */}
          <text x={leftLabelX} y={rowY(0) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Series:
          </text>
          <rect x={leftBoxX} y={rowY(0)} width={leftBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(leftBoxX, rowY(0), leftBoxW, boxH)} fontSize="3" fill="black">
            {d.series || ""}
          </text>

          <text x={rightLabelX} y={rowY(0) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Size:
          </text>
          <rect x={sizeBoxX} y={rowY(0)} width={sizeBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(sizeBoxX, rowY(0), sizeBoxW, boxH)} fontSize="3" fill="black">
            {d.size || ""}
          </text>

          {/* Row 1: Class/Pitch + Op Speed */}
          <text x={leftLabelX} y={rowY(1) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Class / Pitch:
          </text>
          <rect x={leftBoxX} y={rowY(1)} width={leftBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(leftBoxX, rowY(1), leftBoxW, boxH)} fontSize="3" fill="black">
            {d.class_pitch || ""}
          </text>

          <text x={rightLabelX} y={rowY(1) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Op. Speed:
          </text>
          <rect x={rightBoxX} y={rowY(1)} width={rightBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(rightBoxX, rowY(1), rightBoxW, boxH)} fontSize="3" fill="black">
            {d.op_speed || ""}
          </text>
          <text x={rightBoxX + rightBoxW + 1} y={rowY(1) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            RPM
          </text>

          {/* Row 2: Motor + Max Speed */}
          <text x={leftLabelX} y={rowY(2) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Motor:
          </text>
          <rect x={leftBoxX} y={rowY(2)} width={leftBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(leftBoxX, rowY(2), leftBoxW, boxH)} fontSize="3" fill="black">
            {d.motor || ""}
          </text>
          <text x={leftBoxX + leftBoxW + 1} y={rowY(2) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            kW
          </text>

          <text x={rightLabelX} y={rowY(2) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Max Speed:
          </text>
          <rect x={rightBoxX} y={rowY(2)} width={rightBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(rightBoxX, rowY(2), rightBoxW, boxH)} fontSize="3" fill="black">
            {d.op_speed || ""}
          </text>
          <text x={rightBoxX + rightBoxW + 1} y={rowY(2) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            RPM
          </text>

          {/* Row 3: Voltage + Phase */}
          <text x={leftLabelX} y={rowY(3) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Voltage:
          </text>
          <rect x={leftBoxX} y={rowY(3)} width={leftBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(leftBoxX, rowY(3), leftBoxW, boxH)} fontSize="3" fill="black">
            {d.voltage || ""}
          </text>
          <text x={leftBoxX + leftBoxW + 1} y={rowY(3) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            V
          </text>

          <text x={rightLabelX} y={rowY(3) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Phase:
          </text>
          <rect x={rightBoxX} y={rowY(3)} width={rightBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(rightBoxX, rowY(3), rightBoxW, boxH)} fontSize="3" fill="black">
            {d.phase || ""}
          </text>

          {/* Row 4: FLA + Frequency */}
          <text x={leftLabelX} y={rowY(4) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            F.L.A:
          </text>
          <rect x={leftBoxX} y={rowY(4)} width={leftBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(leftBoxX, rowY(4), leftBoxW, boxH)} fontSize="3" fill="black">
            {d.fla || ""}
          </text>

          <text x={rightLabelX} y={rowY(4) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Frequency:
          </text>
          <rect x={rightBoxX} y={rowY(4)} width={rightBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(rightBoxX, rowY(4), rightBoxW, boxH)} fontSize="3" fill="black">
            {d.frequency || ""}
          </text>
          <text x={rightBoxX + rightBoxW + 1} y={rowY(4) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Hz
          </text>

          {/* Row 5: Op Temp + Connection */}
          <text x={leftLabelX} y={rowY(5) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Op Temp:
          </text>
          <rect x={leftSmallBoxX} y={rowY(5)} width={leftSmallBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(leftSmallBoxX, rowY(5), leftSmallBoxW, boxH)} fontSize="3" fill="black">
            {d.op_temp || ""}
          </text>
          <text x={leftSmallBoxX + leftSmallBoxW + 1} y={rowY(5) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            °C
          </text>

          <text x={rightLabelX} y={rowY(5) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Conn:
          </text>
          <rect x={rightBoxX} y={rowY(5)} width={rightBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(rightBoxX, rowY(5), rightBoxW, boxH)} fontSize="3" fill="black">
            {d.connection || ""}
          </text>

          {/* Row 6: Serial + Date */}
          <text x={leftLabelX} y={rowY(6) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Serial No:
          </text>
          <rect x={leftSmallBoxX} y={rowY(6)} width={leftSmallBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(leftSmallBoxX, rowY(6), leftSmallBoxW, boxH)} fontSize="3" fill="black">
            {d.serial_no || ""}
          </text>

          <text x={rightLabelX} y={rowY(6) + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Date of Manuf:
          </text>
          <rect x={rightBoxX} y={rowY(6)} width={rightBoxW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(rightBoxX, rowY(6), rightBoxW, boxH)} fontSize="2.5" fill="black">
            {d.date_of_manuf || ""}
          </text>

          {/* Relube */}
          <text x={leftLabelX} y={relubeY + boxH / 2} textAnchor="start" dominantBaseline="central" fontSize="3" fontWeight="bold">
            Re-Lubrication Interval:
          </text>
          <rect x={relubeX} y={relubeY} width={relubeW} height={boxH} fill="#d9d9d9" stroke="black" strokeWidth="0.5" />
          <text {...boxTextProps(relubeX, relubeY, relubeW, boxH)} fontSize="3" fill="black">
            {d.relube_interval || "N/A"}
          </text>

          {/* Company info */}
          <text x={PLATE_W / 2} y={companyBaseY + 6} textAnchor="middle" fontSize="4" fontWeight="bold" fill="black">
            FAN MOVEMENT (PTY) LTD
          </text>
          <text x={PLATE_W / 2} y={companyBaseY + 11} textAnchor="middle" fontSize="3" fill="black">
            TEL: 011 682 3020
          </text>
          <text x={PLATE_W / 2} y={companyBaseY + 15} textAnchor="middle" fontSize="3" fill="black">
            www.fanmovement.co.za
          </text>
        </svg>
      </div>
    </div>
  );
}
