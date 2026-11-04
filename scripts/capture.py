#!/usr/bin/env python3
"""Renders real screenshots of the watch faces on a running Wear OS emulator/device.

For each scenario the face is regenerated with the scenario's configuration as defaults
(WFF_DEFAULTS), built with Gradle, installed with adb, set as the active watch face and
captured with `screencap`. Nothing is mocked: every PNG is the WFF runtime output.

Usage:
  python3 scripts/capture.py json                 # all scenarios of one face
  python3 scripts/capture.py json developer full  # selected scenarios
  python3 scripts/capture.py --list json
Scenarios live in <face>-developer/generator/scenarios.py (SCENARIOS dict).
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get("ANDROID_HOME", Path.home() / "Android/Sdk"))
ADB = str(SDK / "platform-tools/adb")
FACES = {
    "json": ("json-developer", "json_face.py", "dev.devtime.watchface.json"),
    "code": ("code-developer", "code_face.py", "dev.devtime.watchface.code"),
    "matrix": ("matrix-developer", "matrix_face.py", "dev.devtime.watchface.matrix"),
}


def run(cmd: list[str], env: dict | None = None, check: bool = True) -> str:
    res = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    if check and res.returncode != 0:
        sys.stderr.write(res.stdout + res.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd)}")
    return res.stdout


def adb(*args: str, check: bool = True) -> str:
    return run([ADB, *args], check=check)


def load_scenarios(module: str) -> dict:
    path = ROOT / module / "generator/scenarios.py"
    spec = importlib.util.spec_from_file_location("scenarios", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SCENARIOS


def screencap(dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    png = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True, check=True).stdout
    dest.write_bytes(png)


def set_face(package: str) -> None:
    adb("shell", "am", "broadcast", "-a", "com.google.android.wearable.app.DEBUG_SURFACE",
        "--es", "operation", "set-watchface", "--es", "watchFaceId", package)


def wake() -> None:
    adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    # The HOME key toggles the app launcher on Wear OS; the HOME intent always lands on the watch face.
    adb("shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")


def capture(face: str, names: list[str], out_dir: Path) -> list[Path]:
    module, generator, package = FACES[face]
    scenarios = load_scenarios(module)
    shots = []
    env = dict(os.environ)
    env.setdefault("JAVA_HOME", str(Path.home() / ".local/jdk/jdk-17"))
    env.setdefault("ANDROID_HOME", str(SDK))
    for name in names or list(scenarios):
        sc = scenarios[name]
        env["WFF_DEFAULTS"] = ",".join(f"{k}={v}" for k, v in sc["config"].items())
        print(f"[{face}] {name}: {env['WFF_DEFAULTS']}")
        run([sys.executable, str(ROOT / module / "generator" / generator)], env=env)
        run(["./gradlew", "-q", f":{module}:assembleDebug"], env=env)
        apk = ROOT / module / f"build/outputs/apk/debug/{module}-debug.apk"
        # Uninstall first: the system persists the favorite's style, so a reinstall would keep old values.
        adb("uninstall", package, check=False)
        adb("install", str(apk))
        set_face(package)
        time.sleep(4)
        wake()
        time.sleep(sc.get("settle", 8))
        dest = out_dir / module / f"{name}.png"
        screencap(dest)
        shots.append(dest)
        if sc.get("ambient"):
            adb("shell", "input", "keyevent", "KEYCODE_SLEEP")
            time.sleep(4)
            amb = out_dir / module / f"{name}-aod.png"
            screencap(amb)
            shots.append(amb)
            wake()
            time.sleep(1)
    # Restore the committed defaults so the module is left in its release state.
    env.pop("WFF_DEFAULTS", None)
    run([sys.executable, str(ROOT / module / "generator" / generator)], env=env)
    return shots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("face", choices=FACES)
    ap.add_argument("scenarios", nargs="*")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "reports/screens"))
    args = ap.parse_args()
    if args.list:
        for k, v in load_scenarios(FACES[args.face][0]).items():
            print(f"{k:20s} {v['config']}")
        return
    for p in capture(args.face, args.scenarios, Path(args.out)):
        print(p.relative_to(ROOT))


if __name__ == "__main__":
    main()
