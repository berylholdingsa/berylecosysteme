#!/bin/bash
set -e

export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

echo "Step 1: Updating SDK Components..."
yes | sdkmanager --licenses > /dev/null
sdkmanager --install "platforms;android-36" "build-tools;36.0.0"

echo "Step 2: Fixing Gradle Wrapper (Switching to Stable 9.0)..."
if [ -f "gradle/wrapper/gradle-wrapper.properties" ]; then
    # Utilisation d'une URL ultra-compatible
    sed -i 's|distributionUrl=.*|distributionUrl=https\\://services.gradle.org/distributions/gradle-9.0-bin.zip|' gradle/wrapper/gradle-wrapper.properties
fi

echo "Step 3: Aligning Project Versions..."
find . -name "build.gradle.kts" -exec sed -i 's/compileSdk = .*/compileSdk = 36/' {} +
find . -name "build.gradle.kts" -exec sed -i 's/targetSdk = .*/targetSdk = 36/' {} +
find . -name "build.gradle.kts" -exec sed -i 's/jvmTarget = .*/jvmTarget = "17"/' {} +

if [ -f "gradle/libs.versions.toml" ]; then
    sed -i 's/agp = .*/agp = "8.8.0"/' gradle/libs.versions.toml
    sed -i 's/kotlin = .*/kotlin = "2.1.0"/' gradle/libs.versions.toml
fi

echo "Step 4: Compiling..."
chmod +x gradlew
./gradlew clean assembleDebug
