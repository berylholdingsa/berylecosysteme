#!/bin/bash
set -e

ROOT="$(pwd)"

echo "==> Suppression des scripts de forçage"
rm -f "$ROOT/fix_final.sh" "$ROOT/apply_fix_910.sh" "$ROOT/force_fix.sh"

echo "==> Mise à jour de gradle-wrapper.properties"
WRAPPER="$ROOT/gradle/wrapper/gradle-wrapper.properties"
if [[ -f "$WRAPPER" ]]; then
  sed -i 's#distributionUrl=.*#distributionUrl=https\://services.gradle.org/distributions/gradle-8.10.2-bin.zip#' "$WRAPPER"
else
  echo "Erreur : gradle-wrapper.properties introuvable"
  exit 1
fi

echo "==> Mise à jour de gradle/libs.versions.toml"
VERSIONS="$ROOT/gradle/libs.versions.toml"
if [[ -f "$VERSIONS" ]]; then
  sed -i 's/^agp = ".*"/agp = "8.7.2"/' "$VERSIONS"
else
  echo "Erreur : libs.versions.toml introuvable"
  exit 1
fi

echo "==> Mise à jour des build.gradle.kts"
find "$ROOT" -type f -name "build.gradle.kts" -print0 | while IFS= read -r -d '' file; do
  sed -i 's/9\.0\.0/8.7.2/g' "$file"
done

echo "==> Nettoyage Gradle"
./gradlew clean || true

echo "==> Build test"
./gradlew :app:compileDebugKotlin

echo "==> Fini"
