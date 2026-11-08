#!/bin/sh
set -eu
: "${ANDROID_JAR:?Set ANDROID_JAR to Android API 19 android.jar}"
: "${D8:?Set D8 to the Android SDK d8 executable}"
output=${1:?Pass an absolute output path for monitor.jar}
cd "$(dirname "$0")"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
mkdir -p "$temporary/stubs" "$temporary/classes" "$temporary/dex"
find stubs -name '*.java' > "$temporary/stubs.args"
find src -name '*.java' > "$temporary/sources.args"
javac --release 8 -Xlint:-options -cp "$ANDROID_JAR" -d "$temporary/stubs" @"$temporary/stubs.args"
javac --release 8 -Xlint:-options -cp "$ANDROID_JAR:$temporary/stubs" -d "$temporary/classes" @"$temporary/sources.args"
jar cf "$temporary/classes.jar" -C "$temporary/classes" hmgapi
"$D8" --min-api 19 --lib "$ANDROID_JAR" --classpath "$temporary/stubs" \
    --output "$temporary/dex" "$temporary/classes.jar"
jar cMf "$output" -C "$temporary/dex" classes.dex
