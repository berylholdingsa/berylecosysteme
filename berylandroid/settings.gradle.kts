pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
    plugins {
        kotlin("android") version "2.2.10"
        kotlin("jvm") version "2.2.10"
        id("org.jetbrains.kotlin.plugin.serialization") version "2.2.10"
        id("com.android.application") version "9.0.1"
        id("com.android.library") version "9.0.1"
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven {
            url = uri("https://maven.maplibre.org")
        }
        maven {
            url = uri("https://jitpack.io")
        }
    }
}

rootProject.name = "BerylAndroid"
include(":app")
include(":backend")
include(":backend:sentinel-core")
include(":backend:sentinel-server")
include(":sentinel-sdk")
