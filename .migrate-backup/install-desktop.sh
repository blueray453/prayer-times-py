#!/usr/bin/env bash
#
# install-desktop.sh — install the desktop entry and icon for prayer-times-gui
# ----------------------------------------------------------------------------
# Copies:
#   prayer-times-gui.desktop   → ~/.local/share/applications/   (chmod 777)
#   icons/mosque.png           → ~/.local/share/icons/hicolor/256x256/apps/
#   icons/mosque.png           → ~/.local/share/icons/          (flat copy)
#
# Then runs update-desktop-database and gtk-update-icon-cache if available.
#
# Usage:
#   bash install-desktop.sh
#   bash install-desktop.sh --uninstall
#
set -euo pipefail

# ------------------------------------------------------------------
# Locate the project root (directory containing this script)
# ------------------------------------------------------------------
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DESKTOP_NAME="prayer-times-gui.desktop"
ICON_NAME="mosque.png"

DESKTOP_SRC="$SRC/$DESKTOP_NAME"
ICON_SRC="$SRC/icons/$ICON_NAME"

# ------------------------------------------------------------------
# Destination directories
# ------------------------------------------------------------------
APPS_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
ICON_FLAT_DIR="$HOME/.local/share/icons"
ICON_THEME_DIR="$HOME/.local/share/icons/hicolor"

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
die()  { echo "[FATAL] $*" >&2; exit 1; }
info() { echo "[INFO]  $*"; }

refresh_caches() {
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$ICON_THEME_DIR" >/dev/null 2>&1 || true
    fi
}

# ------------------------------------------------------------------
# Uninstall mode
# ------------------------------------------------------------------
if [[ "${1:-}" == "--uninstall" ]]; then
    info "Removing installed desktop entry and icon…"
    rm -f "$APPS_DIR/$DESKTOP_NAME"
    rm -f "$APPS_DIR/prayer-times.desktop"    # legacy name, if present
    rm -f "$ICON_DIR/$ICON_NAME"
    rm -f "$ICON_FLAT_DIR/$ICON_NAME"
    refresh_caches
    info "Done."
    exit 0
fi

# ------------------------------------------------------------------
# Sanity checks
# ------------------------------------------------------------------
[[ -f "$DESKTOP_SRC" ]] || die "Desktop file not found: $DESKTOP_SRC"
[[ -f "$ICON_SRC"    ]] || die "Icon not found:         $ICON_SRC"

# Make the source copy executable with the same mode so future copies inherit it.
chmod 777 "$DESKTOP_SRC" 2>/dev/null || true

if command -v desktop-file-validate >/dev/null 2>&1; then
    if ! desktop-file-validate "$DESKTOP_SRC"; then
        die "Desktop file failed validation: $DESKTOP_SRC"
    fi
fi

# ------------------------------------------------------------------
# Install
# ------------------------------------------------------------------
info "Source:        $SRC"
info "Desktop file:  $DESKTOP_SRC"
info "Icon file:     $ICON_SRC"
echo

mkdir -p "$APPS_DIR" "$ICON_DIR" "$ICON_FLAT_DIR" "$ICON_THEME_DIR"

cp -f "$DESKTOP_SRC" "$APPS_DIR/$DESKTOP_NAME"
chmod 777 "$APPS_DIR/$DESKTOP_NAME"

cp -f "$ICON_SRC" "$ICON_DIR/$ICON_NAME"
cp -f "$ICON_SRC" "$ICON_FLAT_DIR/$ICON_NAME"

# Remove a stale copy from an earlier install, if any.
rm -f "$APPS_DIR/prayer-times.desktop"

refresh_caches

info "Desktop entry → $APPS_DIR/$DESKTOP_NAME  (mode 777)"
info "Icon (theme)  → $ICON_DIR/$ICON_NAME"
info "Icon (flat)   → $ICON_FLAT_DIR/$ICON_NAME"
echo
info "The launcher should now appear in your application menu."
info "If the icon does not update, log out and back in."
echo
info "To uninstall:  bash $(basename "$0") --uninstall"