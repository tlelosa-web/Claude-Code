-- CreateTable
CREATE TABLE "DeliveryNote" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "dnNumber" TEXT NOT NULL,
    "date" DATETIME NOT NULL,
    "customer" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "DeliveryNote_dnNumber_key" ON "DeliveryNote"("dnNumber");
