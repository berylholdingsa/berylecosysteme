#!/bin/bash
set -e

echo "🚀 [1/6] Initialisation de l'environnement SDK (Standard 2026)..."
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator
mkdir -p $ANDROID_HOME/cmdline-tools

if [ ! -d "$ANDROID_HOME/cmdline-tools/latest" ]; then
    echo "📦 Téléchargement des outils de ligne de commande..."
    wget -q --show-progress https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/cmdline.zip
    unzip -q /tmp/cmdline.zip -d /tmp/cmdline-tools-root
    mv /tmp/cmdline-tools-root/cmdline-tools $ANDROID_HOME/cmdline-tools/latest
    rm -rf /tmp/cmdline.zip /tmp/cmdline-tools-root
fi

echo "🛠️ [2/6] Installation des composants SDK (API 36, Build-tools 36.0.0)..."
yes | sdkmanager --licenses > /dev/null
sdkmanager --install \
    "platform-tools" \
    "build-tools;36.0.0" \
    "platforms;android-36" \
    "emulator" \
    "system-images;android-36;google_apis;x86_64"

echo "🧬 [3/6] Optimisation pour CPU AMD Ryzen (KVM)..."
if [[ $(lsmod | grep kvm_amd) ]]; then
    echo "✅ Accélération KVM AMD active."
else
    echo "⚠️ Activation de KVM..."
    sudo modprobe kvm_amd || echo "❌ Erreur: Vérifiez la virtualisation (SVM) dans votre BIOS."
fi

echo "📱 [4/6] Création de l'émulateur Ryzen_Dev_API36..."
echo "no" | avdmanager create avd \
    --name "Ryzen_Dev_API36" \
    --package "system-images;android-36;google_apis;x86_64" \
    --device "pixel_6" \
    --force
echo "hw.ramSize=4096" >> ~/.android/avd/Ryzen_Dev_API36.avd/config.ini

echo "📝 [5/6] Alignement du projet (Gradle 9.1 / Java 17)..."
if [ -f "gradle/wrapper/gradle-wrapper.properties" ]; then
    sed -i 's|distributionUrl=.*|distributionUrl=https\\://services.gradle.org/distributions/gradle-9.1-bin.zip|' gradle/wrapper/gradle-wrapper.properties
fi

# Mise à jour récursive des fichiers build.gradle.kts
find . -name "build.gradle.kts" -exec sed -i 's/compileSdk = .*/compileSdk = 36/' {} +
find . -name "build.gradle.kts" -exec sed -i 's/targetSdk = .*/targetSdk = 36/' {} +
find . -name "build.gradle.kts" -exec sed -i 's/jvmTarget = .*/jvmTarget = "17"/' {} +

echo "🔍 [6/6] Validation finale..."
echo "-------------------------------------------------------"
echo "SDK: $ANDROID_HOME"
echo "Java: $(java -version 2>&1 | head -n 1)"
echo "Gradle: $(./gradlew --version | grep Gradle || echo 'Gradle wrapper non trouvé')"
echo "-------------------------------------------------------"

echo "🎉 TERMINÉ ! Votre projet est prêt."
