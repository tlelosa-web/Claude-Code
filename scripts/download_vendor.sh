#!/bin/bash
# ============================================
# SOPS — Vendor Library Downloader
# Downloads all required frontend assets
# No internet required at runtime — vendored locally
# ============================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENDOR_DIR="$PROJECT_DIR/static/vendor"

echo "Downloading vendor libraries to $VENDOR_DIR..."

# 1. Tabulator 6.x
echo "  [1/4] Tabulator 6.3.0..."
TABULATOR_DIR="$VENDOR_DIR/tabulator"
mkdir -p "$TABULATOR_DIR"
curl -sL "https://unpkg.com/tabulator-tables@6.3.0/dist/css/tabulator.min.css" -o "$TABULATOR_DIR/tabulator.min.css"
curl -sL "https://unpkg.com/tabulator-tables@6.3.0/dist/js/tabulator.min.js" -o "$TABULATOR_DIR/tabulator.min.js"
echo "       Done."

# 2. Tom Select 2.x
echo "  [2/4] Tom Select 2.3.1..."
TOMSELECT_DIR="$VENDOR_DIR/tom-select"
mkdir -p "$TOMSELECT_DIR"
curl -sL "https://unpkg.com/tom-select@2.3.1/dist/css/tom-select.css" -o "$TOMSELECT_DIR/tom-select.css"
curl -sL "https://unpkg.com/tom-select@2.3.1/dist/js/tom-select.complete.min.js" -o "$TOMSELECT_DIR/tom-select.complete.min.js"
echo "       Done."

# 3. Alpine.js 3.x
echo "  [3/4] Alpine.js 3.14.8..."
ALPINE_DIR="$VENDOR_DIR/alpinejs"
mkdir -p "$ALPINE_DIR"
curl -sL "https://unpkg.com/alpinejs@3.14.8/dist/cdn.min.js" -o "$ALPINE_DIR/alpine.min.js"
echo "       Done."

# 4. Inter font (self-hosted woff2)
echo "  [4/4] Inter font 4.1..."
FONTS_DIR="$VENDOR_DIR/fonts"
mkdir -p "$FONTS_DIR"
curl -sL "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.woff2" -o "$FONTS_DIR/Inter-Regular.woff2"
curl -sL "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-SemiBold.woff2" -o "$FONTS_DIR/Inter-SemiBold.woff2"
curl -sL "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.woff2" -o "$FONTS_DIR/Inter-Bold.woff2"
echo "       Done."

echo ""
echo "All vendor libraries downloaded successfully!"
echo "  - Tabulator 6.3.0"
echo "  - Tom Select 2.3.1"
echo "  - Alpine.js 3.14.8"
echo "  - Inter font 4.1 (Regular, SemiBold, Bold)"
echo ""
echo "Total size:"
du -sh "$VENDOR_DIR"