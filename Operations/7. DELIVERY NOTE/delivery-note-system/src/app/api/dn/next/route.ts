import { NextResponse } from "next/server";
import prisma from "@/lib/prisma";

export async function GET() {
  try {
    const dns = await prisma.deliveryNote.findMany({
      select: { dnNumber: true },
    });

    if (dns.length === 0) {
      return NextResponse.json({ nextDn: "FM-DN0001" });
    }

    // Track the highest numeric-suffixed DN across the whole table, not just
    // the most-recently-created row (see docs/specs/edit-delete-pdf-export-2026-07-17.md Step 0).
    let highest: { prefix: string; number: number; padLength: number } | null = null;

    for (const { dnNumber } of dns) {
      const match = dnNumber.match(/^(.*?)(\d+)$/);
      if (!match) continue; // skip non-matching rows, don't crash

      const prefix = match[1];
      const numberStr = match[2];
      const number = parseInt(numberStr, 10);

      if (!highest || number > highest.number) {
        highest = { prefix, number, padLength: numberStr.length };
      }
    }

    if (!highest) {
      // Theoretical edge case: no row matches the pattern at all. Fall back
      // to the previous single-row behavior using the most-recently-created row.
      const latestDn = await prisma.deliveryNote.findFirst({
        orderBy: { createdAt: "desc" },
      });
      return NextResponse.json({ nextDn: (latestDn?.dnNumber ?? "FM-DN0001") + "-1" });
    }

    const nextNumber = highest.number + 1;
    const nextDn = `${highest.prefix}${nextNumber.toString().padStart(highest.padLength, "0")}`;

    return NextResponse.json({ nextDn });
  } catch (error) {
    console.error("Error fetching next DN:", error);
    return NextResponse.json({ error: "Failed to fetch next DN" }, { status: 500 });
  }
}
