import { NextResponse } from "next/server";
import prisma from "@/lib/prisma";

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await req.json();
    // dnNumber is intentionally never read from the body here — it's the
    // permanent identifier and must not be overwritable via a crafted payload.
    const { date, customer, description } = body;

    if (!date || !customer || !description) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    const existingDn = await prisma.deliveryNote.findUnique({
      where: { id },
    });

    if (!existingDn) {
      return NextResponse.json({ error: "Delivery Note not found" }, { status: 404 });
    }

    const dn = await prisma.deliveryNote.update({
      where: { id },
      data: {
        date: new Date(date),
        customer,
        description,
      },
    });

    return NextResponse.json({ success: true, dn });
  } catch (error) {
    console.error("Error updating DN:", error);
    return NextResponse.json({ error: "Failed to update Delivery Note" }, { status: 500 });
  }
}
