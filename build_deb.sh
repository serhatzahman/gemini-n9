#!/bin/bash
# Gemini N9 - Debian Package Build Script
# Creates a MeeGo 1.2 Harmattan compatible .deb package with gzip compression

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="/tmp/gemini_deb_build"
VERSION=$(grep "Version:" "$SCRIPT_DIR/debian/control" | awk '{print $2}')
OUTPUT_DEB="$SCRIPT_DIR/releases/gemini-n9-v${VERSION}.deb"

echo "=== Building Gemini N9 v${VERSION} for Nokia N9 ==="

# Clean build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/gemini-n9/qml"
mkdir -p "$BUILD_DIR/opt/gemini-n9/icons"
mkdir -p "$BUILD_DIR/usr/share/applications"

# Copy debian control files
cp "$SCRIPT_DIR/debian/control" "$BUILD_DIR/DEBIAN/"
cp "$SCRIPT_DIR/debian/postinst" "$BUILD_DIR/DEBIAN/"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# Copy source files
cp "$SCRIPT_DIR/src/main.py" "$BUILD_DIR/opt/gemini-n9/"
cp "$SCRIPT_DIR/src/gemini_api.py" "$BUILD_DIR/opt/gemini-n9/"
cp "$SCRIPT_DIR/src/qml/"*.qml "$BUILD_DIR/opt/gemini-n9/qml/"
cp "$SCRIPT_DIR/src/icons/"*.png "$BUILD_DIR/opt/gemini-n9/icons/"
cp "$SCRIPT_DIR/src/gemini-n9.desktop" "$BUILD_DIR/usr/share/applications/"

# Set executable permissions
chmod +x "$BUILD_DIR/opt/gemini-n9/main.py"
chmod 644 "$BUILD_DIR/usr/share/applications/gemini-n9.desktop"

# Ensure output directory exists
mkdir -p "$SCRIPT_DIR/releases"

# CRITICAL: MeeGo Harmattan dpkg requires gzip compression (-Zgzip)
echo "Packing with gzip compression..."
dpkg-deb -Zgzip --build "$BUILD_DIR" "$OUTPUT_DEB"

echo "Build successful! Package: $OUTPUT_DEB"
ls -lh "$OUTPUT_DEB"
