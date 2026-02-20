#!/usr/bin/env bash
set -e

SDK_ROOT="$HOME/snap/android-studio/common/Android/Sdk"
CMDLINE="$SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
AVDMANAGER="$SDK_ROOT/cmdline-tools/latest/bin/avdmanager"

echo "== Android SDK bootstrap (Snap) =="

mkdir -p "$SDK_ROOT"

echo "Installing command-line tools..."
mkdir -p "$SDK_ROOT/cmdline-tools"
cd "$SDK_ROOT/cmdline-tools"

if [ ! -d "latest" ]; then
  echo "Command-line tools must be installed via Android Studio first (1-time)."
  echo "More Actions → SDK Manager → SDK Tools → Android SDK Command-line Tools"
  exit 1
fi

echo "Accepting licenses..."
yes | $CMDLINE --licenses

echo "Installing SDK platforms and tools..."
$CMDLINE \
  "platform-tools" \
  "platforms;android-34" \
  "platforms;android-33" \
  "build-tools;34.0.0" \
  "emulator" \
  "system-images;android-34;google_apis;x86_64"

echo "Creating AVD..."
$AVDMANAGER create avd \
  --name Pixel_API_34 \
  --package "system-images;android-34;google_apis;x86_64" \
  --device "pixel_6" \
  --force

echo "SDK bootstrap complete."
echo "Launch emulator via Android Studio or: emulator -avd Pixel_API_34"
