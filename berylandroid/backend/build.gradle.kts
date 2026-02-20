plugins {
    application
    kotlin("jvm")
    id("org.jetbrains.kotlin.plugin.serialization")
}
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

group = "com.beryl.backend"
version = "1.0.0"

val ktorVersion = "2.3.12"

application {
    mainClass.set("ApplicationKt")
}

kotlin {
    jvmToolchain(17)
}

dependencies {
    implementation("io.ktor:ktor-server-core-jvm:$ktorVersion")
    implementation("io.ktor:ktor-server-netty-jvm:$ktorVersion")
    implementation("io.ktor:ktor-server-content-negotiation-jvm:$ktorVersion")
    implementation("io.ktor:ktor-serialization-kotlinx-json-jvm:$ktorVersion")

    testImplementation("io.ktor:ktor-server-test-host-jvm:$ktorVersion")
    testImplementation("io.ktor:ktor-client-content-negotiation-jvm:$ktorVersion")
}

tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
        allWarningsAsErrors.set(false)
    }
    doFirst {
        println(">>> Compiling Kotlin sources for backend")
    }
}
