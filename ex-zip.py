#!/usr/bin/env python3
"""
ex-zip.py — CONTOH pack folder menjadi zip module Magisk (anti-bug backslash).

Basis: https://raw.githubusercontent.com/FaaRamadhann/FAACC/refs/heads/main/zip.py
Bedanya: dibuat generik sebagai template — tinggal ubah blok KONFIG.

Cara pakai:
    python ex-zip.py                  # pack folder script ini -> build/contoh-v<version>.zip
    python ex-zip.py D:\\path\\modul   # pack folder lain
    python ex-zip.py -o rilis.zip     # output build/rilis.zip
    python ex-zip.py --no-version     # output build/contoh.zip tanpa versi

Hasil TIDAK perlu di-commit (tambahkan build/ dan *.zip ke .gitignore).
Distribusi via upload manual ke GitHub Releases.

Catatan backslash (Windows):
    - Script ini TIDAK memakai string path Windows mentah seperti
      "D:\\GitHub-..." di dalam kode. Semua path dibangun dari
      pathlib.Path, jadi bebas error escape backslash.
    - Entry di dalam zip selalu forward-slash (as_posix) agar terbaca
      Magisk/KernelSU. Ini bug umum kalau pakai os.path.join mentah.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import zipfile

# ---------------- KONFIG (ubah sesuai project) ----------------
APP_NAME = "contoh"  # nama default output: build/<APP_NAME>.zip / <APP_NAME>-vX.zip

# File yang wajib ada sebelum di-pack. Kalau hilang -> script berhenti.
# Contoh Magisk minimal: module.prop saja. Tambahkan sesuai kebutuhan.
REQUIRED = [
    "module.prop",
    "customize.sh",
    "uninstall.sh",
    "service.sh",
    "action.sh",
    "system/bin/contoh",
]

# File yang butuh bit executable di dalam zip (Magisk baca external_attr).
EXECUTABLES = {
    "customize.sh",
    "uninstall.sh",
    "service.sh",
    "action.sh",
    "system/bin/contoh",
}

# File/dir yang dikecualikan dari zip (bukan bagian module).
EXCLUDE_DIRS = {
    "temp", "__pycache__", ".git", ".hg", ".svn",
    "archive", "build", "manager",
}
EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db",
    "ex-zip.py", "ex-build.py", "ex-build.bat",
    ".gitignore", ".gitattributes",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".zip"}
# -------------- akhir KONFIG ------------------------------------

ROOT = pathlib.Path(__file__).resolve().parent


def read_version(module_dir: pathlib.Path) -> str:
    """Ambil version=vX dari module.prop. Fallback 1.0.0."""
    prop = module_dir / "module.prop"
    try:
        text = prop.read_text(encoding="utf-8")
    except OSError:
        return "1.0.0"
    m = re.search(r"^version\s*=\s*(.+?)\s*$", text, re.M)
    if not m:
        return "1.0.0"
    return m.group(1).lstrip("v").strip() or "1.0.0"


def should_skip(path: pathlib.Path, module_dir: pathlib.Path) -> bool:
    rel = path.relative_to(module_dir)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    if path.is_file():
        if path.name in EXCLUDE_FILES:
            return True
        if path.name.startswith("session-"):
            return True
        if path.suffix in EXCLUDE_SUFFIXES:
            return True
    return False


def zip_info_for(path: pathlib.Path, arcname_posix: str) -> zipfile.ZipInfo:
    """Buat ZipInfo dengan forward-slash + permission unix yang benar."""
    zi = zipfile.ZipInfo(filename=arcname_posix)
    zi.compress_type = zipfile.ZIP_DEFLATED
    if path.is_dir():
        zi.filename += "/"  # penanda direktori, tetap forward-slash
        zi.external_attr = (0o755 << 16) | 0x10
    else:
        mode = 0o755 if arcname_posix in EXECUTABLES else 0o644
        zi.external_attr = mode << 16
    return zi


def build(module_dir: pathlib.Path, out_zip: pathlib.Path) -> pathlib.Path:
    if not module_dir.is_dir():
        sys.exit("Module dir tidak ketemu: %s" % module_dir)
    missing = [f for f in REQUIRED if not (module_dir / f).exists()]
    if missing:
        sys.exit("File wajib hilang: " + ", ".join(missing))

    # Jangan pack output zip ke dalam dirinya sendiri (kalau out di dalam root).
    out_zip = out_zip.resolve()
    files: list[pathlib.Path] = []
    for p in sorted(module_dir.rglob("*")):
        if p.resolve() == out_zip:
            continue
        if should_skip(p, module_dir):
            continue
        files.append(p)

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            # PENTING: as_posix() -> forward-slash, bukan backslash Windows.
            arc = path.relative_to(module_dir).as_posix()
            zi = zip_info_for(path, arc)
            if path.is_dir():
                zf.writestr(zi, "")
            else:
                zf.writestr(zi, path.read_bytes())

    # Validasi: pastikan tidak ada backslash di entry names.
    with zipfile.ZipFile(out_zip) as zf:
        bad = [n for n in zf.namelist() if "\\" in n]
        if bad:
            sys.exit("ZIP cacat, ada backslash di entry: %s" % bad[:5])

    return out_zip


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pack folder menjadi zip Magisk di build/.")
    ap.add_argument("path", nargs="?", default=".",
                    help="Path module (default: folder script ini / cwd)")
    ap.add_argument("-o", "--output", default=None,
                    help="Nama file output di build/ (default: <APP>-v<version>.zip)")
    ap.add_argument("--no-version", action="store_true",
                    help="Output build/<APP>.zip tanpa versi")
    args = ap.parse_args(argv)

    module_dir = pathlib.Path(args.path).resolve()
    # Kalau path default ".", pakai folder script agar stabil di Windows.
    if args.path == "." and ROOT != pathlib.Path.cwd().resolve():
        # tetap pakai cwd bila user memang menjalankannya dari project lain
        # tanpa argumen? Pilih cwd supaya "copy ke root project lalu jalan"
        # terasa natural seperti ex-build.py.
        module_dir = pathlib.Path.cwd().resolve()

    outdir = module_dir / "build"
    outdir.mkdir(parents=True, exist_ok=True)
    version = read_version(module_dir)
    if args.output:
        out = pathlib.Path(args.output)
        out = out if out.is_absolute() else (outdir / out.name)
    elif args.no_version:
        out = outdir / ("%s.zip" % APP_NAME)
    else:
        out = outdir / ("%s-v%s.zip" % (APP_NAME, version))

    result = build(module_dir, out)
    size_kb = result.stat().st_size / 1024
    print("OK: %s (%.1f KB) dari %s" % (result.name, size_kb, module_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
