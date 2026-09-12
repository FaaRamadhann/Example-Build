# Example-Build — Contoh Build APK Android Tanpa Android Studio

Build APK Android langsung pakai **JDK + Android SDK build-tools**, tanpa Android Studio / Gradle.

Repo ini berisi 2 script yang fungsinya **sama persis**, tinggal pilih salah satu:

| File | Bahasa | Butuh apa | Cocok untuk |
|------|--------|-----------|-------------|
| `ex-build.bat` | Batch (Windows) | JDK + SDK saja | Pemula, klik-jalan, tanpa install Python |
| `ex-build.py` | Python 3 | JDK + SDK + Python 3.8+ | Error lebih jelas, bisa passing path project |

Keduanya melakukan 6 tahap yang sama: `javac → d8 → aapt → keystore → zipalign → apksigner`.

---

## 1. Isi Repo

```
.
├── ex-build.bat      # versi Batch (Windows)
├── ex-build.py       # versi Python (Windows, error lebih jelas)
├── REQUIREMENTS.md   # syarat detail + link download
└── README.md         # file ini
```

> Script ini adalah **contoh/template**. Copy salah satu file ke root project Android kamu, sesuaikan blok `KONFIG`, lalu jalankan.

---

## 2. Syarat (Ringkasan)

1. **JDK 17+** (teruji: JDK 21 LTS) — butuh `javac.exe` + `keytool.exe`
   - Cek: `javac -version`
   - Download: https://adoptium.net
   - JRE saja **tidak cukup**, harus JDK.
2. **Android SDK: 1 build-tools + 1 platform** — butuh `aapt`, `d8`, `zipalign`, `apksigner`
   - Teruji: `build-tools 35.0.0` + `platforms;android-34`
   - Tanpa Android Studio, install via `sdkmanager`:
     ```bat
     sdkmanager "platform-tools" "platforms;android-34" "build-tools;35.0.0"
     ```
   - Download `commandlinetools`: https://developer.android.com/studio#command-line-tools-only
3. **Python 3.8+** — hanya untuk `ex-build.py` (tanpa library tambahan, cuma `os`, `subprocess`, `sys`).
   - Cek: `python --version`
4. **Windows** — kedua script ditulis untuk Windows (path `.exe` / `.bat`).

Detail lengkap + cek cepat ada di [`REQUIREMENTS.md`](REQUIREMENTS.md).

Cek cepat (semua harus ada outputnya):

```bat
javac -version
keytool -help
C:\AndroidSDK\build-tools\35.0.0\aapt.exe version
C:\AndroidSDK\build-tools\35.0.0\d8.bat --version
dir C:\AndroidSDK\platforms\android-34\android.jar
```

Yang **tidak** dibutuhkan: Android Studio, Gradle, adb (cuma perlu pas install APK ke HP), internet (cuma pas download awal).

---

## 3. Struktur Project yang Diharapkan

```
MyApp/
├── AndroidManifest.xml
├── src/
│   └── com/contoh/app/
│       └── MainActivity.java
├── res/                    # opsional, boleh tidak ada
│   ├── values/
│   └── drawable/
├── ex-build.bat            # copy ke sini
└── ex-build.py             # atau yang ini
```

Contoh minimal `AndroidManifest.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.contoh.app">
    <application android:label="Contoh">
        <activity android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

---

## 4. Cara Pakai — `ex-build.bat`

1. Copy `ex-build.bat` ke **root project** (sejajar `AndroidManifest.xml`).
2. Buka file, sesuaikan blok `KONFIG`:

   ```bat
   set "APP_NAME=contoh"
   set "PACKAGE=com.contoh.app"
   set "MIN_SDK=24"
   set "BT=C:\AndroidSDK\build-tools\35.0.0"
   set "PLAT=C:\AndroidSDK\platforms\android-34\android.jar"
   set "JAVA_HOME=C:\Program Files\Java\jdk-21.0.10"
   set "KEYSTORE=debug.keystore"
   set "KEY_ALIAS=contoh"
   set "STOREPASS=android"
   set "KEYPASS=android"
   ```

3. Jalankan dari root project:

   ```bat
   ex-build.bat
   ```

4. Hasil: `build\contoh.apk` (nama sesuai `APP_NAME`, sudah zipalign + signed, siap install).

---

## 5. Cara Pakai — `ex-build.py`

1. Copy `ex-build.py` ke **root project** (atau biarkan di mana saja, tinggal passing path).
2. Sesuaikan blok `KONFIG` di atas file:

   ```python
   APP_NAME = "contoh"
   MIN_SDK = "24"
   BUILD_TOOLS = r"C:\AndroidSDK\build-tools\35.0.0"
   ANDROID_JAR = r"C:\AndroidSDK\platforms\android-34\android.jar"
   JAVA_HOME = r"C:\Program Files\Java\jdk-21.0.10"
   KEYSTORE = "debug.keystore"
   KEY_ALIAS = "contoh"
   STOREPASS = "android"
   KEYPASS = "android"
   ```

3. Jalankan:

   ```bat
   :: build project di folder saat ini
   python ex-build.py

   :: atau build project lain via path
   python ex-build.py D:\path\ke\MyApp
   ```

4. Hasil: `build\contoh.apk` (sama seperti versi `.bat`).

Kelebihan versi Python: tiap command di-print (`  $ ...`), dan kalau gagal langsung keluar pesan `GAGAL (rc=...)` + output 2000 karakter terakhir. Lebih gampang debug.

---

## 6. Alur Build (6 Tahap, Sama di Kedua Script)

| Tahap | Ngapain | Tool |
|-------|---------|------|
| 1/6 | Kumpulkan semua `src\**\*.java` | `for /R` / `os.walk` |
| 2/6 | Compile Java → `.class` | `javac --release 8 -classpath android.jar` |
| 3/6 | Convert `.class` → `classes.dex` | `d8 --min-api` |
| 4/6 | Bungkus `AndroidManifest.xml` (+ `res/` bila ada) + `classes.dex` jadi APK unsigned | `aapt package` + `aapt add` |
| 5/6 | Buat keystore **sekali saja** (dipakai terus) | `keytool -genkeypair` |
| 6/6 | Align + sign + verify | `zipalign` + `apksigner sign` + `apksigner verify` |

Output antara (boleh dihapus, dibuat ulang tiap build):

```
build/
├── sources.txt
├── obj/            # hasil javac (.class)
├── dex/            # hasil d8 (classes.dex)
├── unsigned.apk
├── aligned.apk
└── contoh.apk      # <- HASIL AKHIR
```

---

## 7. Install ke HP

```bat
adb install build\contoh.apk
:: update (tanda -r), wajib key SAMA:
adb install -r build\contoh.apk
```

---

## 8. Troubleshooting

| Gejala | Penyebab / Solusi |
|--------|-------------------|
| `javac is not recognized` | `JAVA_HOME` salah / belum install JDK. Cek `"%JAVA_HOME%\bin\javac.exe"` ada. |
| `android.jar tidak ada` | Path `PLAT` / `ANDROID_JAR` salah. Cek `dir` ke file-nya. |
| `aapt/d8/zipalign/apksigner tidak ditemukan` | Path `BT` / `BUILD_TOOLS` salah atau build-tools belum install via `sdkmanager`. |
| `Tidak ada file .java di src/` | Struktur folder salah. Pastikan `src\**\*.java` ada, dijalankan dari root project. |
| `Bukan project Android: ... tidak ada` (versi py) | `python ex-build.py` dijalankan di folder yang salah, atau pakai argumen path: `python ex-build.py D:\path\MyApp`. |
| APK gagal update di HP (`signatures do not match`) | Ganti keystore. **Backup `debug.keystore`** — update APK wajib pakai key yang sama. |
| Mau ganti nama/paket | Ubah `APP_NAME`, `PACKAGE` (bat) + `package` di `AndroidManifest.xml`, dan path Java di `src/`. |

---

## 9. Catatan Penting

- **Backup `debug.keystore`!** Kalau hilang, kamu tidak bisa update APK di Play Store / HP tanpa uninstall dulu.
- Untuk rilis Play Store, ganti ke keystore sendiri (bukan `debug.keystore`) dengan password kuat, `validity` panjang, dan simpan di tempat aman.
- Di Linux/Mac: ganti `.exe` / `.bat` di KONFIG (`javac`, `d8`, `aapt`, `zipalign`, `apksigner`, `keytool` tanpa ekstensi) dan sesuaikan separator path.

---

## Lisensi

Bebas dipakai untuk project apa pun (contoh/template). Tidak ada garansi.
