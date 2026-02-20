@Suppress("DSL_SCOPE_VIOLATION")
plugins {
    kotlin("jvm")
    alias(libs.plugins.kotlinx.serialization)
    application
}

group = "com.beryl.sentinel"
version = "0.1.0"

kotlin {
    jvmToolchain(17)
}

application {
    mainClass.set("com.beryl.sentinel.server.ApplicationKt")
}

dependencies {
    implementation(project(":backend:sentinel-core"))
    implementation(libs.ktor.server.core)
    implementation(libs.ktor.server.netty)
    implementation(libs.ktor.server.content.negotiation)
    implementation(libs.ktor.serialization.kotlinx.json)
    implementation("io.ktor:ktor-server-call-logging-jvm:${libs.versions.ktor.get()}")
    implementation("io.ktor:ktor-server-status-pages-jvm:${libs.versions.ktor.get()}")
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.logback.classic)

    testImplementation(libs.ktor.server.test.host)
    testImplementation(libs.kotlin.test)
}
