import { NextResponse } from "next/server";
import prisma from "@/lib/prisma";

export async function GET() {
  try {
    const latestDn = await prisma.deliveryNote.findFirst({
      orderBy: { createdAt: "desc" },
    });

    if (!latestDn) {
      return NextResponse.json({ nextDn: "FM-DN0001" });
    }

    const currentDn = latestDn.dnNumber; // e.g. FM-DN0054
    const match = currentDn.match(/^(.*?)(\d+)$/);

    if (!match) {
      return NextResponse.json({ nextDn: currentDn + "-1" });
    }

    const prefix = match[1];
    const numberStr = match[2];
    const nextNumber = parseInt(numberStr, 10) + 1;
    const nextDn = `${prefix}${nextNumber.toString().padStart(numberStr.length, "0")}`;

    return NextResponse.json({ nextDn });
  } catch (error) {
    console.error("Error fetching next DN:", error);
    return NextResponse.json({ error: "Failed to fetch next DN" }, { status: 500 });
  }
}
