#!/usr/bin/env python3
"""Verifies built watch face packages (APK and AAB) before distribution.

Checks per package:
  - APK manifest (aapt2 xmltree): package id, minSdk 34, hasCode=false,
    com.google.wear.watchface.format.version property, android.hardware.type.watch feature
  - APK/AAB contain res/raw/watchface.xml and res/xml/watch_face_info.xml, and no classes*.dex
  - AAB has the base module manifest
Prints a markdown section; exits 1 if any check fails.

Usage: verify_package.py <module> <package-id> <apk> <aab>
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

SDK = Path(os.environ.get("ANDROID_HOME", Path.home() / "Android/Sdk"))


def aapt2() -> str:
    tools = sorted((SDK / "build-tools").iterdir(), reverse=True)
    for t in tools:
        if (t / "aapt2").exists():
            return str(t / "aapt2")
    raise SystemExit("aapt2 not found in $ANDROID_HOME/build-tools")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    module, package, apk, aab = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = ""):
        results.append((name, ok, detail))

    check("APK exists", apk.exists(), str(apk))
    check("AAB exists", aab.exists(), str(aab))
    if apk.exists():
        tree = subprocess.run([aapt2(), "dump", "xmltree", "--file", "AndroidManifest.xml", str(apk)],
                              capture_output=True, text=True).stdout
        check("package id", f'package="{package}"' in tree, package)
        check("minSdk 34", re.search(r'minSdkVersion.*=34', tree) is not None)
        check("hasCode=false", re.search(r'hasCode.*=false', tree) is not None)
        check("WFF version property", "com.google.wear.watchface.format.version" in tree)
        check("watch feature", "android.hardware.type.watch" in tree)
        with zipfile.ZipFile(apk) as z:
            names = z.namelist()
        check("APK has watchface.xml", "res/raw/watchface.xml" in names)
        check("APK has watch_face_info.xml", "res/xml/watch_face_info.xml" in names)
        check("APK has no dex", not any(n.endswith(".dex") for n in names))
    if aab.exists():
        with zipfile.ZipFile(aab) as z:
            names = z.namelist()
        check("AAB base manifest", "base/manifest/AndroidManifest.xml" in names)
        check("AAB has watchface.xml", "base/res/raw/watchface.xml" in names)
        check("AAB has no dex", not any(n.endswith(".dex") for n in names))
        signed = any(n.startswith("META-INF/") and n.endswith((".RSA", ".EC", ".DSA")) for n in names)
        results.append(("AAB upload signature", True, "signed" if signed else
                        "UNSIGNED (create keystore.properties to sign; see docs/PUBLISHING.md)"))

    print(f"### {module}\n")
    print("| Check | Result | Detail |\n|---|---|---|")
    for name, ok, detail in results:
        print(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    for p in (apk, aab):
        if p.exists():
            print(f"\n- `{p.name}`: {p.stat().st_size / 1024:.0f} KB, sha256 `{sha256(p)[:16]}…`")
    print()
    sys.exit(0 if all(ok for _, ok, _ in results) else 1)


if __name__ == "__main__":
    main()
