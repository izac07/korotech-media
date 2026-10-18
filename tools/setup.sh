#!/usr/bin/env bash
# Prépare une machine (routine cloud ou PC Linux/macOS) pour rendre les reels.
# Usage : source tools/setup.sh      -> exporte $PY (l'interpréteur à utiliser : "$PY" tools/motion.py ...)
# tools/motion.py exige Python >= 3.12 (f-strings imbriquées). Testé le 18/10/2026 sur l'environnement cloud :
# python3 = 3.11 (refusé), python3.13 présent, ffmpeg 6.1 présent, modules absents, pip rattaché à 3.13.
set -u

PY=""
for cand in python3.13 python3.12 python3; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
    PY="$(command -v "$cand")"; break
  fi
done
if [ -z "$PY" ]; then
  echo "ERREUR setup : aucun Python >= 3.12 (tools/motion.py ne tourne pas en dessous)"; return 1 2>/dev/null || exit 1
fi
echo "setup : Python = $PY ($("$PY" --version 2>&1))"

if ! "$PY" -c 'import playwright, numpy, scipy, PIL' 2>/dev/null; then
  "$PY" -m pip install --quiet --break-system-packages playwright numpy scipy pillow 2>/dev/null \
    || "$PY" -m pip install --quiet --user playwright numpy scipy pillow
fi
# Chromium pour Playwright (+ bibliothèques système si on a les droits)
"$PY" -m playwright install --with-deps chromium >/dev/null 2>&1 || "$PY" -m playwright install chromium >/dev/null 2>&1

for outil in ffmpeg ffprobe; do
  command -v "$outil" >/dev/null 2>&1 || { echo "ERREUR setup : $outil absent"; return 1 2>/dev/null || exit 1; }
done

# Chromium qui démarre vraiment. Si celui de Playwright manque (cloud : téléchargement bloqué, seul un build
# préinstallé dans /opt/pw-browsers), on prend un Chromium déjà présent et on l'exporte dans PW_CHROMIUM
# (lu par tools/korotech.py et tools/audit.py).
essai_chromium() {  # $1 = chemin d'un exécutable, ou vide pour le Chromium de Playwright
  PW_TEST="$1" "$PY" - <<'EOF' >/dev/null 2>&1
import os
from playwright.sync_api import sync_playwright
kw = {"executable_path": os.environ["PW_TEST"]} if os.environ.get("PW_TEST") else {}
with sync_playwright() as p:
    b = p.chromium.launch(**kw); pg = b.new_page(); pg.set_content("<p>ok</p>"); b.close()
EOF
}
unset PW_CHROMIUM
if ! essai_chromium ""; then
  for c in /opt/pw-browsers/chromium-*/chrome-linux*/chrome /opt/pw-browsers/chromium_headless_shell-*/chrome-*/chrome-headless-shell \
           "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome "$(command -v chromium 2>/dev/null)" "$(command -v chromium-browser 2>/dev/null)" \
           "$(command -v google-chrome 2>/dev/null)"; do
    [ -n "$c" ] && [ -x "$c" ] && essai_chromium "$c" && { export PW_CHROMIUM="$c"; break; }
  done
  if [ -z "${PW_CHROMIUM:-}" ]; then
    echo "ERREUR setup : aucun Chromium ne démarre (ni celui de Playwright, ni un préinstallé)"; return 1 2>/dev/null || exit 1
  fi
fi
"$PY" -c 'import numpy, scipy, PIL' || { echo "ERREUR setup : modules"; return 1 2>/dev/null || exit 1; }
echo "setup : OK (modules + Chromium${PW_CHROMIUM:+ préinstallé : $PW_CHROMIUM})"
export PY
