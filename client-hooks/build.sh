#!/bin/sh
set -eu
: "${ANDROID_JAR:?Set ANDROID_JAR}"
: "${HMG_RUNTIME:?Set HMG_RUNTIME to compiled HMG-API runtime classes}"
: "${R8_JAR:?Set R8_JAR}"
output=${1:?Pass an absolute output path for hooks.jar}
cd "$(dirname "$0")"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
mkdir -p "$temporary/classes" "$temporary/dex"
javac --release 8 -Xlint:-options -cp "$ANDROID_JAR:$HMG_RUNTIME" -d "$temporary/classes" src/*.java
jar cf "$temporary/classes.jar" -C "$temporary/classes" hmgapi
java -cp "$R8_JAR" com.android.tools.r8.D8 --min-api 19 --lib "$ANDROID_JAR" --classpath "$HMG_RUNTIME" --output "$temporary/dex" "$temporary/classes.jar"
jar cMf "$output" -C "$temporary/dex" classes.dex
