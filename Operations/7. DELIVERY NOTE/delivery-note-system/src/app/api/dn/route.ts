import { NextResponse } from "next/server";
import prisma from "@/lib/prisma";

export async function GET() {
  try {
    const dns = await prisma.deliveryNote.findMany({
      orderBy: { createdAt: "desc" },
    });

    return NextResponse.json(dns);
  } catch (error) {
    console.error("Error fetching DNs:", error);
    return NextResponse.json({ error: "Failed to fetch Delivery Notes" }, { status: 500 });
  }
}
