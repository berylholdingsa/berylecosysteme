plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.google.services)
}

android {
    namespace = "com.beryl.berylandroid"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.beryl.berylandroid"
        minSdk = 26
        targetSdk = 36
        versionCode = 10
        versionName = "2.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        val sentinelApiKey = project.findProperty("SENTINEL_API_KEY")?.toString()
            ?: "TODO_SET_SENTINEL_API_KEY"
        val sentinelApiSecret = project.findProperty("SENTINEL_API_SECRET")?.toString()
            ?: "TODO_SET_SENTINEL_API_SECRET"
        // Configure BERYLPAY_BASE_URL_DEBUG in gradle.properties:
        // Emulator: http://10.0.2.2:8080/
        // Physical device: http://<LOCAL_IP>:8080/
        val berylPayBaseUrlDebug = project.findProperty("BERYLPAY_BASE_URL_DEBUG")?.toString()
            ?: "http://localhost:8080/"
        val berylPayBaseUrlProd = project.findProperty("BERYLPAY_BASE_URL_PROD")?.toString()
            ?: "https://api.berylpay.com/"
        val berylPayCertPinPrimary = project.findProperty("BERYLPAY_CERT_PIN_PRIMARY")?.toString()
            ?: ""
        val berylPayCertPinBackup = project.findProperty("BERYLPAY_CERT_PIN_BACKUP")?.toString()
            ?: ""
        val esgBaseUrl = project.findProperty("ESG_BASE_URL")?.toString()
            ?: ""
        val greenOsBearerToken = project.findProperty("GREENOS_BEARER_TOKEN")?.toString()
            ?: ""
        buildConfigField("String", "SENTINEL_API_KEY", "\"$sentinelApiKey\"")
        buildConfigField("String", "SENTINEL_API_SECRET", "\"$sentinelApiSecret\"")
        buildConfigField("String", "BASE_URL_DEBUG", "\"$berylPayBaseUrlDebug\"")
        buildConfigField("String", "BASE_URL_PROD", "\"$berylPayBaseUrlProd\"")
        buildConfigField("String", "BERYLPAY_CERT_PIN_PRIMARY", "\"$berylPayCertPinPrimary\"")
        buildConfigField("String", "BERYLPAY_CERT_PIN_BACKUP", "\"$berylPayCertPinBackup\"")
        buildConfigField("String", "ESG_BASE_URL", "\"$esgBaseUrl\"")
        buildConfigField("String", "GREENOS_BEARER_TOKEN", "\"$greenOsBearerToken\"")
        buildConfigField("long", "SEARCH_DEBOUNCE_MS", "250L")
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

dependencies {
    // Firebase
    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.auth.ktx)
    implementation(libs.firebase.ui.auth)
    implementation("com.google.firebase:firebase-firestore-ktx")
    implementation("com.google.firebase:firebase-storage-ktx")

    // Core & Lifecycle
    implementation(libs.core.ktx)
    implementation(libs.appcompat)
    implementation(libs.material)
    implementation(libs.lifecycle.runtime.compose)

    // Jetpack Compose
    implementation(platform(libs.compose.bom))
    implementation(libs.ui)
    implementation(libs.material3)
    implementation(libs.activity.compose)
    implementation(libs.ui.tooling.preview)
    implementation(libs.material.icons.extended)
    implementation(libs.navigation.compose)
    implementation(libs.ui.text.google.fonts)
    implementation(libs.play.services.auth)
    implementation("org.maplibre.gl:android-sdk:10.2.0")
    implementation("androidx.datastore:datastore-preferences:1.1.1")
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")

    implementation(project(":sentinel-sdk"))

    debugImplementation(libs.ui.tooling)
    testImplementation(libs.kotlin.test)
    testImplementation("junit:junit:4.13.2")
}
