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
    mainClass.set("com.beryl.sentinel.ApplicationKt")
}

dependencies {
    implementation(libs.ktor.server.core)
    implementation(libs.ktor.server.netty)
    implementation(libs.ktor.server.content.negotiation)
    implementation("io.ktor:ktor-server-status-pages-jvm:${libs.versions.ktor.get()}")
    implementation(libs.ktor.serialization.kotlinx.json)
    implementation("com.google.firebase:firebase-admin:9.2.0")
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.logback.classic)
    implementation(libs.exposed.core)
    implementation(libs.exposed.dao)
    implementation(libs.exposed.jdbc)
    implementation(libs.exposed.java.time)
    implementation(libs.hikaricp)
    implementation(libs.postgresql)

    testImplementation(libs.kotlin.test)
    testImplementation(libs.ktor.server.test.host)
    testImplementation(libs.h2)
}
