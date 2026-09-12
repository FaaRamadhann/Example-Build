"""
ex-build.py — CONTOH build APK Android TANPA Android Studio (versi Python).
Sama persis dengan ex-build.bat, tapi lintas-platform dan error-nya jelas.

Cara pakai:
    python ex-build.py [path-project]      # default: folder saat ini

Struktur project yang diharapkan:
    AndroidManifest.xml
    src/**/*.java        (kode sumber)
    res/...              (opsional, boleh tidak ada)

Hasil: build/<APP_NAME>.apk (sudah zipalign + signed)
"""

import os
import subprocess
import sys

# ---------------- KONFIG (ubah sesuai project) ----------------
APP_NAME = "contoh"
MIN_SDK = "24"
BUILD_TOOLS = r"C:\AndroidSDK\build-tools\35.0.0"
ANDROID_JAR = r"C:\AndroidSDK\platforms\android-34\android.jar"
JAVA_HOME = r"C:\Program Files\Java\jdk-21.0.10"
KEYSTORE = "debug.keystore"   # relatif ke root project
KEY_ALIAS = "contoh"
STOREPASS = "android"
KEYPASS = "android"
# -------------- akhir KONFIG ------------------------------------


def run(cmd, cwd):
    """Jalankan command, raise SystemExit bila gagal (dengan output)."""
    print("  $", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:] if r.stdout else "")
        print(r.stderr[-2000:] if r.stderr else "")
        sys.exit(f"GAGAL (rc={r.returncode}): {cmd[0]}")
    return r


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    for must in ("AndroidManifest.xml", "src"):
        if not os.path.exists(os.path.join(root, must)):
            sys.exit(f"Bukan project Android: {must} tidak ada di {root}")

    javac = os.path.join(JAVA_HOME, "bin", "javac.exe")
    keytool = os.path.join(JAVA_HOME, "bin", "keytool.exe")
    d8 = os.path.join(BUILD_TOOLS, "d8.bat")
    aapt = os.path.join(BUILD_TOOLS, "aapt.exe")
    zipalign = os.path.join(BUILD_TOOLS, "zipalign.exe")
    apksigner = os.path.join(BUILD_TOOLS, "apksigner.bat")
    build = os.path.join(root, "build")
    os.makedirs(os.path.join(build, "obj"), exist_ok=True)
    os.makedirs(os.path.join(build, "dex"), exist_ok=True)

    print("[1/6] kumpulkan source...")
    sources = []
    for dp, _, fns in os.walk(os.path.join(root, "src")):
        sources += [os.path.join(dp, f) for f in fns if f.endswith(".java")]
    if not sources:
        sys.exit("Tidak ada file .java di src/")
    print(f"  {len(sources)} file java")

    print("[2/6] javac...")
    with open(os.path.join(build, "sources.txt"), "w") as fh:
        fh.write("\n".join(sources))
    run([javac, "--release", "8", "-classpath", ANDROID_JAR,
         "-d", os.path.join(build, "obj"),
         "@" + os.path.join(build, "sources.txt")], root)

    print("[3/6] d8 (java -> dex)...")
    classes = []
    for dp, _, fns in os.walk(os.path.join(build, "obj")):
        classes += [os.path.join(dp, f) for f in fns if f.endswith(".class")]
    run([d8, "--min-api", MIN_SDK, "--lib", ANDROID_JAR,
         "--output", os.path.join(build, "dex")] + classes, root)

    print("[4/6] aapt package...")
    cmd = [aapt, "package", "-f", "-M", "AndroidManifest.xml"]
    if os.path.isdir(os.path.join(root, "res")):
        cmd += ["-S", "res"]
    cmd += ["-I", ANDROID_JAR, "-F", os.path.join(build, "unsigned.apk")]
    run(cmd, root)
    run([aapt, "add", os.path.join(build, "unsigned.apk"), "classes.dex"],
        os.path.join(build, "dex"))

    print("[5/6] keystore (sekali saja, lalu dipakai terus)...")
    print("  PENTING: backup debug.keystore — update APK wajib key yang sama!")
    ks = os.path.join(root, KEYSTORE)
    if not os.path.exists(ks):
        run([keytool, "-genkeypair", "-keystore", ks, "-alias", KEY_ALIAS,
             "-keyalg", "RSA", "-keysize", "2048", "-validity", "10950",
             "-storepass", STOREPASS, "-keypass", KEYPASS,
             "-dname", f"CN={APP_NAME}"], root)

    print("[6/6] zipalign + apksigner...")
    run([zipalign, "-f", "4", os.path.join(build, "unsigned.apk"),
         os.path.join(build, "aligned.apk")], root)
    out_apk = os.path.join(build, f"{APP_NAME}.apk")
    run([apksigner, "sign", "--ks", ks, "--ks-key-alias", KEY_ALIAS,
         "--ks-pass", f"pass:{STOREPASS}", "--key-pass", f"pass:{KEYPASS}",
         "--out", out_apk, os.path.join(build, "aligned.apk")], root)
    run([apksigner, "verify", out_apk], root)

    print(f"\nSELESAI: {out_apk}")


if __name__ == "__main__":
    main()
