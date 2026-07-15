import { NextResponse } from "next/server";
import prisma from "@/lib/prisma";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { dnNumber, date, customer, description } = body;

    if (!dnNumber || !date || !customer || !description) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    // Check for duplicate DN
    const existingDn = await prisma.deliveryNote.findUnique({
      where: { dnNumber },
    });

    if (existingDn) {
      return NextResponse.json({ error: "Delivery Note number already exists" }, { status: 400 });
    }

    const dn = await prisma.deliveryNote.create({
      data: {
        dnNumber,
        date: new Date(date),
        customer,
        description,
      },
    });

    return NextResponse.json({ success: true, dn });
  } catch (error) {
    console.error("Error registering DN:", error);
    return NextResponse.json({ error: "Failed to register Delivery Note" }, { status: 500 });
  }
}
