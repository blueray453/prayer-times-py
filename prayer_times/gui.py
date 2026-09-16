#!/usr/bin/env python3
"""
prayer_times.gui — Prayer Times GUI (Solarized dark)
----------------------------------------------------
Thin PySide6 wrapper around prayer_times.cli. Imports the CLI as a
sibling module and calls its internal functions directly.

Configuration is loaded from ~/.config/prayer-times/config.json. On
first run, the template shipped inside the package is copied there.
Press R (or Ctrl+R) in the running window to reload the file.

The mode radio buttons switch between fixed / pcd / spa at runtime and
update the results immediately. The chosen mode is NOT written back to
the JSON — the file is the single source of truth.

Install:  pipx install .
Run:      prayer-times-gui
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from importlib.resources import files as _pkg_files

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QScrollArea,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import QTimer, Qt, QDateTime
from PySide6.QtGui import QFont, QShortcut, QKeySequence

# Sibling module inside the same package
from . import cli as ptc

# ==================================================================
# Config file handling (Pattern A: packaged template, user copy)
# ==================================================================

TEMPLATE_NAME = "config.json"  # inside the package
CONFIG_NAME = "config.json"  # user file name

def _config_dir() -> Path:
    """Resolve ~/.config/prayer-times/ honoring XDG_CONFIG_HOME."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "prayer-times"

CONFIG_DIR = _config_dir()
CONFIG_PATH = CONFIG_DIR / CONFIG_NAME

def _read_template() -> dict:
    """Load the packaged template as a dict."""
    resource = _pkg_files(__package__).joinpath(TEMPLATE_NAME)
    return json.loads(resource.read_text(encoding="utf-8"))

def _normalize(cfg: dict, defaults: dict) -> dict:
    """Merge user config over defaults and coerce types."""
    out = dict(defaults)
    out.update({k: cfg[k] for k in defaults if k in cfg})

    # Resolve "date": null means today
    if not out.get("date"):
        out["date"] = datetime.now().strftime("%Y-%m-%d")

    # Coerce numeric fields
    for k in ("lat", "lon", "elev", "fajr_angle", "isha_angle", "temperature", "pressure", "asr_ratio", "asr_early"):
        try:
            out[k] = float(out[k])
        except (TypeError, ValueError):
            out[k] = defaults[k]

    # Coerce string fields and validate enumerations
    out["tz"] = str(out["tz"])
    out["shafaq"] = str(out["shafaq"])
    out["mode"] = str(out["mode"])

    if out["mode"] not in ("fixed", "pcd", "spa"):
        out["mode"] = "fixed"
    if out["shafaq"] not in ("general", "ahmer", "abyad"):
        out["shafaq"] = "general"

    return out

def load_config() -> dict:
    """
    Load the user config. On first run, copy the packaged template
    to ~/.config/prayer-times/config.json and use that.
    """
    defaults = _read_template()

    if not CONFIG_PATH.exists():
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            # Byte-for-byte copy so JSON formatting is preserved
            with _pkg_files(__package__).joinpath(TEMPLATE_NAME).open("rb") as src:
                with open(CONFIG_PATH, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            print(f"[INFO] Created default config at {CONFIG_PATH}", file=sys.stderr)
        except OSError as e:
            print(f"[WARN] Could not create {CONFIG_PATH}: {e}", file=sys.stderr)
        return _normalize(defaults, defaults)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"[WARN] Could not read {CONFIG_PATH}: {e}. Using defaults.", file=sys.stderr)
        return _normalize(defaults, defaults)

    return _normalize(raw, defaults)

# ==================================================================
# Fonts and theme
# ==================================================================

FONT_TITLE = 30
FONT_CLOCK = 22
FONT_GROUP = 16
FONT_LABEL = 15
FONT_RADIO = 16
FONT_PRAYER = 20
FONT_TIME = 22
FONT_BEST = 15
FONT_FORBID = 17
FONT_STATUS = 15
FONT_NOTE = 13
FONT_HEADER_COL = 14
FONT_HINT = 12

THEME = {
    "bg": "#002b36",
    "panel_bg": "#073642",
    "blue": "#268bd2",
    "cyan": "#2aa198",
    "green": "#859900",
    "magenta": "#d33682",
    "muted": "#93a1a1",
    "orange": "#cb4b16",
    "red": "#dc322f",
    "text": "#839496",
    "violet": "#6c71c4",
    "yellow": "#b58900",
}

def theme_stylesheet() -> str:
    return f"""
        QMainWindow {{ background-color: {THEME['bg']}; }}
        QLabel {{ color: {THEME['text']}; background: transparent; }}
        QGroupBox {{
            color: {THEME['cyan']};
            border: 1px solid {THEME['muted']};
            border-radius: 4px;
            margin-top: 22px;
            padding-top: 18px;
            font-weight: bold;
            font-size: {FONT_GROUP}px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            left: 12px;
            color: {THEME['cyan']};
        }}
        QRadioButton {{
            color: {THEME['text']};
            padding: 6px;
            font-size: {FONT_RADIO}px;
            spacing: 10px;
        }}
        QRadioButton::indicator {{
            width: 18px; height: 18px;
            border-radius: 9px;
            border: 2px solid {THEME['muted']};
            background: {THEME['panel_bg']};
        }}
        QRadioButton::indicator:checked {{
            background: {THEME['blue']};
            border: 2px solid {THEME['blue']};
        }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollArea > QWidget > QWidget {{ background: transparent; }}
    """

# ==================================================================
# Main window
# ==================================================================

class PrayerTimesGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prayer Times — Hadith-Based Calculator")
        self.setMinimumSize(1100, 950)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(theme_stylesheet())

        self.config = load_config()
        self.state = {
            "result": None,
            "src": ("fixed", "fixed"),
            "tz_label": "",
            "fajr_angle": None,
            "isha_angle": None,
        }

        self._setup_ui()
        self._setup_clock()
        self._setup_shortcuts()
        self._sync_radio_from_config()
        self._recalculate()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(14)
        root.setContentsMargins(28, 22, 28, 22)

        # ---------- Header ----------
        header = QWidget()
        hl = QVBoxLayout(header)
        hl.setSpacing(2)
        hl.setAlignment(Qt.AlignCenter)

        title = QLabel("PRAYER TIMES  —  HADITH-BASED CALCULATOR")
        title.setStyleSheet(f"color: {THEME['green']};")
        title.setFont(QFont("Helvetica", FONT_TITLE, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(f"color: {THEME['yellow']};")
        self.clock_label.setFont(QFont("Helvetica", FONT_CLOCK, QFont.Bold))
        self.clock_label.setAlignment(Qt.AlignCenter)
        hl.addWidget(self.clock_label)

        self.hint_label = QLabel(f"Config: {CONFIG_PATH}   ·   press R to reload from file")
        self.hint_label.setStyleSheet(f"color: {THEME['muted']};")
        self.hint_label.setFont(QFont("Helvetica", FONT_HINT))
        self.hint_label.setAlignment(Qt.AlignCenter)
        hl.addWidget(self.hint_label)

        root.addWidget(header)

        # ---------- Mode radio bar ----------
        mode_bar = QWidget()
        mb = QHBoxLayout(mode_bar)
        mb.setContentsMargins(0, 0, 0, 0)
        mb.setSpacing(24)
        mb.setAlignment(Qt.AlignCenter)

        mode_lbl = QLabel("Mode:")
        mode_lbl.setStyleSheet(f"color: {THEME['cyan']}; font-weight: bold;")
        mode_lbl.setFont(QFont("Helvetica", FONT_RADIO, QFont.Bold))
        mb.addWidget(mode_lbl)

        self.rb_fixed = QRadioButton("Fixed angles")
        self.rb_pcd = QRadioButton("PCD dynamic")
        self.rb_spa = QRadioButton("PCD + NREL SPA")

        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.addButton(self.rb_fixed, 0)
        self.mode_btn_group.addButton(self.rb_pcd, 1)
        self.mode_btn_group.addButton(self.rb_spa, 2)
        self.mode_btn_group.buttonClicked.connect(self._on_mode_changed)

        mb.addWidget(self.rb_fixed)
        mb.addWidget(self.rb_pcd)
        mb.addWidget(self.rb_spa)

        root.addWidget(mode_bar)

        # ---------- Divider ----------
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"color: {THEME['muted']};")
        root.addWidget(div)

        # ---------- Results (full width, scrollable) ----------
        right_inner = QWidget()
        self.right_layout = QVBoxLayout(right_inner)
        self.right_layout.setSpacing(16)
        self.right_layout.setAlignment(Qt.AlignTop)

        self.status_label = QLabel("Calculating…")
        self.status_label.setStyleSheet(f"color: {THEME['cyan']}; font-size: {FONT_STATUS}px; font-weight: bold;")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(self.status_label)

        # Prayer windows
        self.prayer_group = QGroupBox("Prayer Windows")
        self.prayer_grid = QGridLayout(self.prayer_group)
        self.prayer_grid.setSpacing(10)
        self.prayer_grid.setColumnStretch(1, 1)
        self.prayer_grid.setColumnStretch(2, 1)
        self.right_layout.addWidget(self.prayer_group)

        # Solar noon anchors
        self.noon_group = QGroupBox("Solar Noon Anchors")
        self.noon_grid = QGridLayout(self.noon_group)
        self.noon_grid.setSpacing(10)
        self.noon_grid.setColumnStretch(1, 1)
        self.right_layout.addWidget(self.noon_group)

        # Forbidden intervals
        self.forbidden_group = QGroupBox("Three Forbidden Times  (Sahih Muslim 831)")
        self.forbidden_grid = QGridLayout(self.forbidden_group)
        self.forbidden_grid.setSpacing(10)
        self.forbidden_grid.setColumnStretch(1, 1)
        self.right_layout.addWidget(self.forbidden_group)

        # Notes
        self.notes_label = QLabel()
        self.notes_label.setWordWrap(True)
        self.notes_label.setStyleSheet(f"color: {THEME['muted']}; font-size: {FONT_NOTE}px; "
                                       f"background-color: {THEME['panel_bg']}; "
                                       f"padding: 14px; border-radius: 6px;")
        self.right_layout.addWidget(self.notes_label)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_inner)
        root.addWidget(right_scroll)

    # ------------------------------------------------------------------
    # Clock
    # ------------------------------------------------------------------
    def _setup_clock(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_clock)
        self.timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        self.clock_label.setText(QDateTime.currentDateTime().toString("hh:mm:ss AP   ·   dddd, MMMM d yyyy"))

    # ------------------------------------------------------------------
    # Shortcuts
    # ------------------------------------------------------------------
    def _setup_shortcuts(self):
        QShortcut(QKeySequence("R"), self, activated=self._reload_from_file)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self._reload_from_file)

    def _reload_from_file(self):
        self.config = load_config()
        self._sync_radio_from_config()
        self._recalculate()

    # ------------------------------------------------------------------
    # Mode handling
    # ------------------------------------------------------------------
    def _current_mode(self) -> str:
        if self.rb_spa.isChecked():
            return "spa"
        if self.rb_pcd.isChecked():
            return "pcd"
        return "fixed"

    def _sync_radio_from_config(self):
        mode = self.config.get("mode", "fixed")
        btn = {
            "fixed": self.rb_fixed,
            "pcd": self.rb_pcd,
            "spa": self.rb_spa,
        }.get(mode, self.rb_fixed)
        btn.setChecked(True)

    def _on_mode_changed(self):
        # Mode change is ephemeral — the JSON file is the source of truth.
        self._recalculate()

    # ------------------------------------------------------------------
    # Recalculate + render
    # ------------------------------------------------------------------
    def _recalculate(self):
        cfg = self.config
        mode = self._current_mode()

        try:
            d = datetime.strptime(cfg["date"], "%Y-%m-%d").date()
        except ValueError:
            self._show_error(f"Invalid date in config: {cfg['date']}")
            return

        try:
            tz_offset, tz_label = ptc.parse_tz(cfg["tz"], d)
        except SystemExit as e:
            self._show_error(f"Timezone error: {e}")
            return

        temperature = float(cfg["temperature"])
        pressure = float(cfg["pressure"])

        try:
            if mode == "fixed":
                fajr_angle = float(cfg["fajr_angle"])
                isha_angle = float(cfg["isha_angle"])
                fajr_src = isha_src = "fixed"
            else:
                fajr_angle, isha_angle = ptc.get_pcd_angles(
                    d,
                    lat=cfg["lat"],
                    lng=cfg["lon"],
                    elevation=cfg["elev"],
                    temperature=temperature,
                    pressure=pressure,
                    shafaq=cfg["shafaq"],
                )
                fajr_src = isha_src = "PCD"
        except Exception as e:
            self._show_error(f"Angle computation error: {e}")
            return

        try:
            r = ptc.calculate(
                d.year,
                d.month,
                d.day,
                cfg["lat"],
                cfg["lon"],
                tz_offset,
                fajr_angle,
                isha_angle,
                float(cfg["asr_ratio"]),
                float(cfg["asr_early"]),
                mode,
                cfg["elev"],
                temperature,
                pressure,
            )
        except Exception as e:
            self._show_error(f"Calculation error: {e}")
            return

        self.state["result"] = r
        self.state["src"] = (fajr_src, isha_src)
        self.state["tz_label"] = tz_label
        self.state["fajr_angle"] = fajr_angle
        self.state["isha_angle"] = isha_angle

        self._render_results()

    def _show_error(self, msg: str):
        self.status_label.setText(f"⚠  {msg}")
        self.status_label.setStyleSheet(f"color: {THEME['red']}; font-size: {FONT_STATUS}px; font-weight: bold;")

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _clear_grid(self, grid):
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _render_results(self):
        r = self.state["result"]
        if not r:
            return
        fmt = ptc.fmt_ampm
        span = ptc.span

        mode = self._current_mode()
        fajr_src, isha_src = self.state["src"]
        mode_label = {
            "fixed": "FIXED ANGLES",
            "pcd": "PCD DYNAMIC",
            "spa": "PCD + NREL SPA",
        }[mode]

        self.status_label.setText(f"{mode_label}   ·   "
                                  f"Fajr = {self.state.get('fajr_angle','?')}° ({fajr_src})   ·   "
                                  f"Isha = {self.state.get('isha_angle','?')}° ({isha_src})   ·   "
                                  f"{self.config['date']}   ·   "
                                  f"{self.config['lat']:.4f}°, {self.config['lon']:.4f}°   ·   "
                                  f"{self.state['tz_label']}")
        self.status_label.setStyleSheet(f"color: {THEME['cyan']}; font-size: {FONT_STATUS}px; font-weight: bold;")

        # ---- Prayer windows ----
        self._clear_grid(self.prayer_grid)

        hdr_style = f"color: {THEME['cyan']}; font-weight: bold; font-size: {FONT_HEADER_COL}px;"
        name_style = f"color: {THEME['text']}; font-weight: bold; font-size: {FONT_PRAYER}px;"
        time_style = f"color: {THEME['text']}; font-size: {FONT_TIME}px;"
        forbid_style = f"color: {THEME['red']}; font-size: {FONT_FORBID}px; font-style: italic;"
        best_style = f"color: {THEME['yellow']}; font-size: {FONT_BEST}px;"

        for col, txt in enumerate(["", "WINDOW", "BEST TIME"]):
            lbl = QLabel(txt)
            lbl.setStyleSheet(hdr_style)
            self.prayer_grid.addWidget(lbl, 0, col)

        rows = [
            ("Fajr", (r["fajr"], r["sunrise"]), f"best: {fmt(r['fajr'])}", False),
            ("Forbidden", (r["sunrise"], r["spear"]), "(sun begins to rise → fully up)", True),
            ("Ishraq", (r["spear"], r["zenith_start"]), f"best: {fmt(r['spear'])}", False),
            ("Duha", (r["spear"], r["zenith_start"]), f"best: {span(r['duha_best_start'], r['duha_best_end'])}",
             False),
            ("Forbidden", (r["zenith_start"], r["zenith_end"]), "(sun at height → passes meridian)", True),
            ("Dhuhr", (r["dhuhr"], r["asr"]), f"best: {fmt(r['dhuhr'])}", False),
            ("Asr", (r["asr"], r["yellow"]), f"best: {span(r['asr'], r['asr_early_end'])} (pray early)", False),
            ("Forbidden", (r["yellow"], r["maghrib"]), "(sun draws near to setting → sets)", True),
            ("Maghrib", (r["maghrib"], r["isha"]), f"best: {fmt(r['maghrib'])}", False),
            ("Isha", (r["isha"], r["midnight"]), f"best: {span(r['isha_best_start'], r['midnight'])}", False),
            ("Tahajjud", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}", False),
            ("Witr", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}", False),
        ]

        for i, (name, win, best, is_forb) in enumerate(rows, start=1):
            nl = QLabel(name)
            nl.setStyleSheet(forbid_style if is_forb else name_style)
            self.prayer_grid.addWidget(nl, i, 0)

            wl = QLabel(span(*win) if win else "—")
            wl.setStyleSheet(forbid_style if is_forb else time_style)
            self.prayer_grid.addWidget(wl, i, 1)

            bl = QLabel(best)
            bl.setStyleSheet(forbid_style if is_forb else best_style)
            self.prayer_grid.addWidget(bl, i, 2)

        # ---- Solar noon anchors ----
        self._clear_grid(self.noon_grid)
        anchors = [
            ("Istiwa' — sun at zenith (peak)", fmt(r["istiwa"])),
            ("Zawal — sun begins decline", fmt(r["zawal"])),
            (f"Dhuhr opens (Zawal + {ptc.DHUHR_OFFSET_MINUTES} min)", fmt(r["dhuhr"])),
            ("Zenith precaution begins", fmt(r["zenith_start"])),
            ("Zenith precaution ends", fmt(r["zenith_end"])),
        ]
        for i, (k, v) in enumerate(anchors):
            kl = QLabel(k)
            kl.setStyleSheet(f"color: {THEME['text']}; font-size: {FONT_LABEL}px;")
            vl = QLabel(v)
            vl.setStyleSheet(f"color: {THEME['violet']}; font-size: {FONT_TIME}px; font-weight: bold;")
            vl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.noon_grid.addWidget(kl, i, 0)
            self.noon_grid.addWidget(vl, i, 1)

        # ---- Forbidden intervals ----
        self._clear_grid(self.forbidden_grid)
        fb = [
            ("1.  Sun begins to rise → fully up", span(r["sunrise"], r["spear"])),
            ("2.  Sun at height → passes meridian", span(r["zenith_start"], r["zenith_end"])),
            ("3.  Sun draws near to setting → sets", span(r["yellow"], r["maghrib"])),
        ]
        for i, (k, v) in enumerate(fb):
            kl = QLabel(k)
            kl.setStyleSheet(f"color: {THEME['red']}; font-size: {FONT_LABEL}px;")
            vl = QLabel(v)
            vl.setStyleSheet(f"color: {THEME['orange']}; font-size: {FONT_TIME}px; font-weight: bold;")
            vl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.forbidden_grid.addWidget(kl, i, 0)
            self.forbidden_grid.addWidget(vl, i, 1)

        # ---- Notes ----
        self.notes_label.setText("NOTE ON SAHIH AL-BUKHARI 586\n"
                                 "\"There is no prayer after the morning prayer till the sun rises, "
                                 "and there is no prayer after the 'Asr prayer till the sun sets.\"\n\n"
                                 "This additional prohibition is not computed separately because its "
                                 "start depends on when you personally finish praying Fajr or Asr, "
                                 "it overlaps with the three intervals above, and it is a nafl-only "
                                 "restriction — the obligatory prayers remain valid in their windows.")

# ==================================================================
# Entry point
# ==================================================================

def main():
    app = QApplication(sys.argv)
    window = PrayerTimesGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
