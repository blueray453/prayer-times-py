APP       := prayer-times
GUI       := prayer-times-gui
PKG       := prayer_times
VENV      := .venv
PY        := $(VENV)/bin/python
VERSION   := $(shell sed -n 's/^__version__ *= *"\(.*\)"/\1/p' src/$(PKG)/__init__.py)
DEB_FILE  := dist/$(APP)_$(VERSION)_all.deb

PREFIX    ?= $(HOME)/.local
APPS_DIR  := $(PREFIX)/share/applications
ICON_DIR  := $(PREFIX)/share/icons/hicolor/256x256/apps
CONF_DIR  := $(or $(XDG_CONFIG_HOME),$(HOME)/.config)/$(APP)

# wherever pipx is configured to put executables
BIN_DIR    = $(shell pipx environment --value PIPX_BIN_DIR 2>/dev/null || echo $(HOME)/.local/bin)

.DEFAULT_GOAL := help
.PHONY: help dev run run-cli install install-dev desktop uninstall purge \
        check fix build deb-deps deb-version deb deb-lint deb-install \
        deb-uninstall deb-clean clean distclean doctor

help:  ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | \
	  awk -F':.*## ' '{printf "  make %-14s %s\n", $$1, $$2}'

# ---------- local development ----------
$(VENV)/.stamp: pyproject.toml
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -e '.[dev]'
	touch $@

dev: $(VENV)/.stamp  ## Create venv and install in editable mode

run: dev  ## Run the GUI from source (no system install)
	$(PY) -m $(PKG)

run-cli: dev  ## Show CLI help from source (pass ARGS="--lat ... ")
	$(PY) -m $(PKG).cli $(ARGS)

# ---------- deploy to this machine (pipx) ----------
install:  ## Install via pipx
	pipx install --force .
	$(MAKE) desktop
	@echo "Installed. Launch with '$(GUI)' or from the app menu."

install-dev:  ## Same as install, but editable (code changes apply live)
	pipx install --force --editable .
	$(MAKE) desktop

desktop:  ## Install .desktop file and icon (absolute Exec path)
	desktop-file-validate data/$(GUI).desktop
	install -d $(APPS_DIR)
	sed 's|^Exec=.*|Exec=$(BIN_DIR)/$(GUI)|' data/$(GUI).desktop > $(APPS_DIR)/$(GUI).desktop
	chmod 644 $(APPS_DIR)/$(GUI).desktop
	install -Dm644 data/icons/hicolor/256x256/apps/$(APP).png $(ICON_DIR)/$(APP).png
	-update-desktop-database $(APPS_DIR)
	-gtk-update-icon-cache -f -t $(PREFIX)/share/icons/hicolor

uninstall:  ## Remove pipx app, menu entry, icon (keeps config)
	-pipx uninstall $(APP)
	rm -f $(APPS_DIR)/$(GUI).desktop $(ICON_DIR)/$(APP).png
	-update-desktop-database $(APPS_DIR)
	-gtk-update-icon-cache -f -t $(PREFIX)/share/icons/hicolor
	@echo "Config ($(CONF_DIR)) kept. 'make purge' removes it."

purge:  ## Delete user config (asks first)
	@read -p "Delete $(CONF_DIR)? [y/N] " a; \
	  [ "$$a" = y ] && rm -rf "$(CONF_DIR)" && echo removed || echo aborted

# ---------- Debian package ----------
deb-deps:  ## Install tools needed to build the .deb (uses sudo)
	sudo apt install build-essential devscripts debhelper dh-python \
	  pybuild-plugin-pyproject python3-all python3-setuptools lintian \
	  desktop-file-utils

deb-version:  ## Add a debian/changelog entry for the current __version__
	@[ -n "$(VERSION)" ] || { echo "could not read version"; exit 1; }
	@if head -1 debian/changelog | grep -q "($(VERSION))"; then \
	  echo "changelog already at $(VERSION)"; \
	else \
	  dch --newversion $(VERSION) --distribution unstable "Release $(VERSION)"; \
	fi

deb:  ## Build the .deb into dist/
	@[ -z "$$VIRTUAL_ENV" ] || { echo "deactivate your venv first"; exit 1; }
	@[ -n "$(VERSION)" ] || { echo "could not read version"; exit 1; }
	@head -1 debian/changelog | grep -q "($(VERSION))" || \
	  { echo "debian/changelog is not at $(VERSION). Run: make deb-version"; exit 1; }
	chmod +x debian/rules
	dpkg-buildpackage -us -uc -b
	mkdir -p dist
	mv -f ../$(APP)_$(VERSION)_* dist/
	@echo "Built: $(DEB_FILE)"

deb-lint:  ## Run lintian on the built package
	lintian --info dist/$(APP)_$(VERSION)_*.changes

deb-install:  ## Install the built .deb (resolves dependencies via apt)
	@[ -f "$(DEB_FILE)" ] || { echo "$(DEB_FILE) not found. Run: make deb"; exit 1; }
	sudo apt install ./$(DEB_FILE)

deb-uninstall:  ## Remove the .deb (keeps user config)
	sudo apt remove $(APP)

deb-clean:  ## Remove debian build leftovers
	rm -rf debian/.debhelper debian/$(APP) debian/files debian/*.substvars \
	       debian/*.debhelper.log debian/debhelper-build-stamp .pybuild

# ---------- quality / packaging ----------
check: dev  ## Lint code and validate .desktop
	$(VENV)/bin/ruff check src
	desktop-file-validate data/$(GUI).desktop

fix: dev  ## Auto-fix lint problems where safe
	$(VENV)/bin/ruff check --fix src

build: dev  ## Build Python sdist + wheel into dist/ (for pip users)
	$(PY) -m build

clean: deb-clean  ## Remove build artifacts
	rm -rf build dist src/*.egg-info
	find . -name __pycache__ -prune -exec rm -rf {} +

distclean: clean  ## clean + remove .venv
	rm -rf $(VENV)

doctor:  ## Check system prerequisites
	@for c in python3 pipx desktop-file-validate; do \
	  command -v $$c >/dev/null && echo "ok      $$c" || echo "MISSING $$c"; done
	@for c in dpkg-buildpackage dch lintian; do \
	  command -v $$c >/dev/null && echo "ok      $$c (deb)" || echo "MISSING $$c (only needed for make deb)"; done
	@echo "version: $(VERSION)"
	@echo "pipx bin dir: $(BIN_DIR)"
