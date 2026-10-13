# Runtime = Astral python-build-standalone (PBS), includes python.exe + stdlib + pip + dynamic tkinter
# Run from git-bash:  bash build.sh            (uses cached download if present)
# DOWNLOAD=1 bash build.sh (force re-download)
# Output:  dist/cascade-<version>.zip  and  dist/cascade-<version>/  (unzipped)

set -euo pipefail

PBS_TAG="20260901"
PBS_PY="3.14.7"          # this tag ships CPython 3.14.7 (venv here is 3.14.5 — same ABI, fine)
PBS_TRIPLE="x86_64-pc-windows-msvc"
PBS_FILE="cpython-${PBS_PY}+${PBS_TAG}-${PBS_TRIPLE}-install_only.tar.gz"
PBS_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PBS_TAG}/${PBS_FILE}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VERSION="$(sed -n "s/^__version__ = '\([0-9.]*\)'$/\1/p" src/__init__.py)"
if [[ -z "$VERSION" ]]; then
    echo "ERROR: could not read version from src/__init__.py" >&2
    exit 1
fi

DIST="dist/cascade-${VERSION}"
DOWNLOAD_DIR="downloads"
PBS_ARCHIVE="${DOWNLOAD_DIR}/${PBS_FILE}"
RUNTIME="${DIST}/runtime"
ZIP="${DIST}.zip"

# Absolute form of RUNTIME — the pip/python calls happen after `cd` into other
# dirs, so a relative path here would break (step 7 cd's into $DIST first).
RUNTIME_ABS="${ROOT}/${RUNTIME}"

# ---------------------------------------------------------------------------
# 1. Download PBS (cached unless DOWNLOAD=1).
# ---------------------------------------------------------------------------
mkdir -p "$DOWNLOAD_DIR"
if [[ ! -f "$PBS_ARCHIVE" ]] || [[ "${DOWNLOAD:-0}" == "1" ]]; then
    echo ">> Downloading PBS ${PBS_FILE} ..."
    curl -fL --noproxy '*' -o "$PBS_ARCHIVE" "$PBS_URL"
else
    echo ">> PBS archive cached at ${PBS_ARCHIVE} (pass DOWNLOAD=1 to refresh)"
fi

# ---------------------------------------------------------------------------
# 2. Fresh dist folder.
# ---------------------------------------------------------------------------
rm -rf "$DIST"
mkdir -p "$DIST"

# ---------------------------------------------------------------------------
# 3. Extract PBS into runtime/.
#    PBS install_only is a FULL normal layout (no python314._pth pinning), so
#    nothing extra is needed — unlike the python.org embeddable.
# ---------------------------------------------------------------------------
echo ">> Extracting PBS into ${RUNTIME} ..."
mkdir -p "$RUNTIME"
tar -xzf "$PBS_ARCHIVE" -C "$RUNTIME" --strip-components=1
# ---------------------------------------------------------------------------
# 4. Install runtime deps INTO the PBS runtime.
#    The pip run MUST NOT be able to see any package from the host machine:
#    pip resolves a requirement against the whole interpreter environment it is
#    handed, and one that is already present in the host's roaming user-site
#    counts as "satisfied" and is never copied into our site-packages. The
#    bundle then dies on the target machine the moment something imports it
#    (found the hard way: requests, urllib3, six and pycparser stayed behind in
#    %APPDATA%\Python\Python314\site-packages, so the backend died on
#    "import syncedlyrics" before it could even write a log line).
#    `-I` (isolated) is what actually enforces this: it drops the user-site and
#    ignores PYTHON* environment variables. PYTHONNOUSERSITE=1 alone is NOT
#    enough - keep it only for the runtime-side calls further down.
#    PBS ships pip, but bootstrap via get-pip.py as a fallback.
# ---------------------------------------------------------------------------
PY="$(find "$RUNTIME_ABS" -maxdepth 1 -name 'python*.exe' | sort | head -1)"
if [[ -z "$PY" ]]; then
    echo "ERROR: no python.exe found under ${RUNTIME_ABS}" >&2
    exit 1
fi

if ! "$PY" -I -m pip --version >/dev/null 2>&1; then
    echo ">> PBS has no pip - bootstrapping get-pip.py ..."
    curl -fL --noproxy '*' -o "${DOWNLOAD_DIR}/get-pip.py" \
        https://bootstrap.pypa.io/get-pip.py
    "$PY" -I "${DOWNLOAD_DIR}/get-pip.py"
fi

echo ">> Installing runtime dependencies into runtime/ ..."
"$PY" -I -m pip install --no-warn-script-location \
    -r requirements.txt

# ---------------------------------------------------------------------------
# 4b. Verify the install the way the bundle will actually run (no user-site).
#     Every pinned requirement must be visible to the bundled interpreter, and
#     pip must see a consistent environment. A quietly incomplete site-packages
#     ships a bundle that only breaks on the target machine, so fail the build
#     here instead of there.
# ---------------------------------------------------------------------------
echo ">> Verifying the dependency set ..."
REQUIRED_LIST="${DOWNLOAD_DIR}/required.tmp"
INSTALLED_LIST="${DOWNLOAD_DIR}/installed.tmp"
tr -d '\r' < requirements.txt \
    | sed -e 's/#.*//' -e '/^[[:space:]]*-/d' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e '/^$/d' \
    | sed -e 's/[<>=!~;].*//' | tr 'A-Z' 'a-z' | tr '_' '-' | sort -u > "$REQUIRED_LIST"
"$PY" -I -m pip list --format=freeze \
    | sed -e 's/[<>=!~].*//' | tr 'A-Z' 'a-z' | tr '_' '-' | sort -u > "$INSTALLED_LIST"
NOT_INSTALLED="$(comm -23 "$REQUIRED_LIST" "$INSTALLED_LIST")"
if [[ -n "$NOT_INSTALLED" ]]; then
    echo "ERROR: these pinned requirements are NOT installed in the runtime:" >&2
    echo "$NOT_INSTALLED" | sed 's/^/  /' >&2
    exit 1
fi
if ! PIP_CHECK="$("$PY" -I -m pip check 2>&1)"; then
    echo "ERROR: pip check reports an inconsistent environment:" >&2
    echo "$PIP_CHECK" | sed 's/^/  /' >&2
    exit 1
fi
echo ">> Dependency set verified."

# ---------------------------------------------------------------------------
# 5. Copy src/, res/ and user docs into the bundle root; prune __pycache__.
# ---------------------------------------------------------------------------
echo ">> Copying src/, res/, docs into bundle root ..."
cp -r src "$DIST/src"
cp -r res "$DIST/res"
cp README.md CHANGELOG.md LICENSE TODO.md "$DIST/" 2>/dev/null || true
find "$DIST/src" "$DIST/res" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ---------------------------------------------------------------------------
# 6. Launcher. `python -m src` reaches cli.py main (src/__main__.py); the
#    backend/hotkey/tray/lyric/dash spawns resolve via sys.executable inside the
#    bundle, so everything stays self-contained. Force CRLF for cmd.
#    No VLC paths are exported here: this bundle does not ship a VLC runtime, so
#    python-vlc auto-detects the machine's own VLC install (registry plus the
#    usual install directories). See the note printed at the end of the build.
# ---------------------------------------------------------------------------
echo ">> Writing launcher cascade.cmd ..."
cat > "$DIST/cascade.cmd" <<'EOF'
@echo off
cd /d "%~dp0"
set PYTHONNOUSERSITE=1
"%~dp0runtime\python.exe" -m src %*
EOF
sed -i 's/$/\r/' "$DIST/cascade.cmd"

# ---------------------------------------------------------------------------
# 7. Zip it. git-bash has no `zip`; use Python stdlib (zipfile) — present in
#    the bundle runtime AND any system python. Skips __pycache__ while packing.
# ---------------------------------------------------------------------------
echo ">> Zipping ${ZIP} ..."
(cd "$DIST" && PYTHONNOUSERSITE=1 "$(dirname "$PY")/python.exe" - <<'EOF'
import os
import zipfile

root = os.getcwd()
out = os.path.join(os.path.dirname(root), os.path.basename(root) + '.zip')

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != '__pycache__']
        for name in filenames:
            full = os.path.join(dirpath, name)
            arc = os.path.relpath(full, os.path.dirname(root))
            zf.write(full, arc)
print(out)
EOF
)
cd "$ROOT"

echo ""
echo "Done."
echo "  unpacked: ${DIST}"
echo "  zip:      ${ZIP}"
du -sh "$DIST" 2>/dev/null | awk '{print "  size:    "$1}'