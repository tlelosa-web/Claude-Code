import { NextResponse } from "next/server";
import { PDFDocument, StandardFonts, rgb } from "pdf-lib";
import prisma from "@/lib/prisma";

export const runtime = "nodejs";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const dn = await prisma.deliveryNote.findUnique({
      where: { id },
    });

    if (!dn) {
      return NextResponse.json({ error: "Delivery Note not found" }, { status: 404 });
    }

    const pdfDoc = await PDFDocument.create();
    const page = pdfDoc.addPage([595.28, 841.89]); // A4 in points
    const { width } = page.getSize();

    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const boldFont = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

    const margin = 50;
    let y = 780;

    page.drawText("Fan Movement (Pty) Ltd — Delivery Note", {
      x: margin,
      y,
      size: 18,
      font: boldFont,
      color: rgb(0.1, 0.1, 0.1),
    });

    y -= 50;

    const fields: [string, string][] = [
      ["DN Number", dn.dnNumber],
      ["Date", new Date(dn.date).toLocaleDateString()],
      ["Customer", dn.customer],
      ["Description", dn.description],
    ];

    for (const [label, value] of fields) {
      page.drawText(`${label}:`, {
        x: margin,
        y,
        size: 12,
        font: boldFont,
        color: rgb(0.1, 0.1, 0.1),
      });
      page.drawText(value, {
        x: margin + 150,
        y,
        size: 12,
        font,
        color: rgb(0.1, 0.1, 0.1),
      });
      y -= 30;
    }

    y -= 60;

    page.drawText("Received by: ______________________", {
      x: margin,
      y,
      size: 12,
      font,
      color: rgb(0.1, 0.1, 0.1),
    });

    page.drawText("Date: ______________________", {
      x: width - margin - 200,
      y,
      size: 12,
      font,
      color: rgb(0.1, 0.1, 0.1),
    });

    const pdfBytes = await pdfDoc.save();

    return new NextResponse(Buffer.from(pdfBytes), {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${dn.dnNumber}.pdf"`,
      },
    });
  } catch (error) {
    console.error("Error generating DN PDF:", error);
    return NextResponse.json({ error: "Failed to generate Delivery Note PDF" }, { status: 500 });
  }
}
