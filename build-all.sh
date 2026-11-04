#!/usr/bin/env bash
# DevTime Watch Faces - build automation.
#
#   ./build-all.sh                 generate + validate + APK + AAB + verify, all faces
#   ./build-all.sh json|code|matrix   same, one face
#   ./build-all.sh validate        generate + schema/semantic validation only
#   ./build-all.sh screenshots [json|code|matrix]   real captures on a running emulator/device
#   ./build-all.sh assets          icons, previews, store assets (needs screenshots)
#   ./build-all.sh clean
#
# Outputs: dist/<face>/*.apk|*.aab, reports/build-report.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

export JAVA_HOME="${JAVA_HOME:-$HOME/.local/jdk/jdk-17}"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export PATH="$JAVA_HOME/bin:$PATH"

declare -A MODULE=([json]=json-developer [code]=code-developer [matrix]=matrix-developer)
declare -A GENERATOR=([json]=json_face.py [code]=code_face.py [matrix]=matrix_face.py)
declare -A PACKAGE=([json]=dev.devtime.watchface.json [code]=dev.devtime.watchface.code [matrix]=dev.devtime.watchface.matrix)
VALIDATOR="shared/scripts/wff-validator/build/install/wff-validator/bin/wff-validator"
REPORT="reports/build-report.md"

log() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

require_env() {
    [[ -x "$JAVA_HOME/bin/java" ]] || die "JDK 17 not found (set JAVA_HOME)"
    [[ -d "$ANDROID_HOME/platforms" ]] || die "Android SDK not found (set ANDROID_HOME)"
    [[ -f local.properties ]] || echo "sdk.dir=$ANDROID_HOME" > local.properties
}

build_validator() {
    if [[ ! -x "$VALIDATOR" ]]; then
        log "building wff-validator (Kotlin)"
        ./gradlew -q -p shared/scripts/wff-validator installDist
    fi
}

generate() {
    local f=$1
    log "generating ${MODULE[$f]}"
    python3 "${MODULE[$f]}/generator/${GENERATOR[$f]}"
}

validate() {
    local f=$1
    log "validating ${MODULE[$f]} (WFF v2 XSD + semantic checks)"
    "$VALIDATOR" shared/wff-spec "${MODULE[$f]}" | tee -a reports/validation.log
}

build_face() {
    local f=$1 m=${MODULE[$f]}
    generate "$f"
    validate "$f"
    log "building $m APK (debug) and AAB (release)"
    ./gradlew -q ":$m:assembleDebug" ":$m:bundleRelease"
    local version
    version=$(sed -n 's/.*versionName = "\(.*\)".*/\1/p' "$m/build.gradle.kts")
    mkdir -p "dist/$m"
    cp "$m/build/outputs/apk/debug/$m-debug.apk" "dist/$m/$m-$version-debug.apk"
    cp "$m/build/outputs/bundle/release/$m-release.aab" "dist/$m/$m-$version-release.aab"
    python3 scripts/verify_package.py "$m" "${PACKAGE[$f]}" \
        "dist/$m/$m-$version-debug.apk" "dist/$m/$m-$version-release.aab" >> "$REPORT"
}

start_report() {
    mkdir -p reports
    : > reports/validation.log
    {
        echo "# Build report"
        echo
        echo "- Date: $(date -u '+%Y-%m-%d %H:%M UTC')"
        echo "- JDK: $("$JAVA_HOME/bin/java" -version 2>&1 | head -1)"
        echo "- Watch Face Format: v2 (minSdk 34 / Wear OS 5)"
        echo
    } > "$REPORT"
}

finish_report() {
    { echo "## Validation"; echo; echo '```'; cat reports/validation.log; echo '```'; } >> "$REPORT"
    log "report: $REPORT"
    ls -la dist/*/ 2>/dev/null || true
}

cmd=${1:-all}
case "$cmd" in
    all)
        require_env; build_validator; start_report
        for f in json code matrix; do build_face "$f"; done
        finish_report ;;
    json|code|matrix)
        require_env; build_validator; start_report
        build_face "$cmd"
        finish_report ;;
    validate)
        require_env; build_validator; mkdir -p reports; : > reports/validation.log
        for f in json code matrix; do generate "$f"; validate "$f"; done ;;
    screenshots)
        require_env
        for f in ${2:-json code matrix}; do python3 scripts/capture.py "$f"; done ;;
    assets)
        python3 shared/scripts/make_icons.py
        python3 scripts/store_assets.py ;;
    clean)
        ./gradlew -q clean
        rm -rf dist reports/build-report.md reports/validation.log ;;
    *)
        sed -n '2,12p' "$0"; exit 2 ;;
esac
