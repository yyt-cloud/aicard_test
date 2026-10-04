#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SOURCE_DIR=$(CDPATH= cd -- "$PROJECT_DIR/.." && pwd)
mkdir -p "$PROJECT_DIR/www" "$PROJECT_DIR/resources"
cp "$SOURCE_DIR/voice-first-feed-eyes-overlay.html" "$PROJECT_DIR/www/index.html"
cp "$SOURCE_DIR/glass-window-icon-02-clear-component-eyes.svg" "$PROJECT_DIR/resources/icon.svg"
echo "Web assets prepared."
