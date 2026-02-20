# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Android app (Jetpack Compose UI, Firebase auth/storage/firestore).
- `sentinel-sdk/`: Android library consumed by the app.
- `backend/sentinel-core/`: Ktor core services and domain logic.
- `backend/sentinel-server/`: Ktor server entrypoint and routing.
- `gradle/`, `build.gradle.kts`, `settings.gradle.kts`: Gradle build configuration.
- `firebase.json`, `firestore.rules`, `firestore.indexes.json`: Firebase configuration.

## Build, Test, and Development Commands
Use Gradle from the repo root:
- `./gradlew assembleDebug` — build the Android debug APK.
- `./gradlew test` — run unit tests for all modules.
- `./gradlew connectedAndroidTest` — run Android instrumentation tests on a device/emulator.
- `./gradlew :backend:sentinel-core:test` — run backend core tests only.
- `./gradlew :backend:sentinel-server:run` — run the Ktor server locally.

## Coding Style & Naming Conventions
- Kotlin/Java: 4-space indentation; target Java 17 (see module configs).
- Android namespaces: `com.beryl.berylandroid` (app), `com.beryl.sentinel.sdk` (SDK).
- Compose UI lives under `app/src/main/java/.../ui` and `.../screens`.
- Keep resource names lowercase with underscores (Android convention), e.g., `ic_launcher_foreground.xml`.

## Testing Guidelines
- Unit tests: `app/src/test`, `backend/**/src/test` (JUnit/Kotlin test + Ktor test host).
- Instrumentation tests: `app/src/androidTest` (AndroidX runner).
- Name tests `*Test.kt` (e.g., `ProfileValidationTest.kt`).

## Commit & Pull Request Guidelines
- Commit messages generally follow Conventional Commit style (`feat(android): ...`, `Fix ...`).
- Use clear, scoped subjects; mention affected module when possible.
- PRs should include: a short description, linked issue (if any), and screenshots for UI changes.
- Note any Firebase/Android SDK setup steps that reviewers must replicate.

## Configuration & Secrets
- Android SDK path is typically set in `local.properties`.
- Firebase config is expected in `app/google-services.json` (do not share secrets in PRs).
