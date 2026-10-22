import java.io.FileInputStream
import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

android {
    namespace = "com.ciheul.helpdesk.helpdesk_mobile"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // Unique Application ID
        applicationId = "com.ciheul.helpdesk.helpdesk_mobile"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            val keyAliasProp = keystoreProperties.getProperty("keyAlias") ?: System.getenv("KEY_ALIAS")
            val keyPasswordProp = keystoreProperties.getProperty("keyPassword") ?: System.getenv("KEY_PASSWORD")
            val storeFileProp = keystoreProperties.getProperty("storeFile") ?: System.getenv("STORE_FILE")
            val storePasswordProp = keystoreProperties.getProperty("storePassword") ?: System.getenv("STORE_PASSWORD")

            if (storeFileProp != null && keyAliasProp != null) {
                keyAlias = keyAliasProp
                keyPassword = keyPasswordProp
                storeFile = file(storeFileProp)
                storePassword = storePasswordProp
            }
        }
    }

    buildTypes {
        release {
            val releaseSigning = signingConfigs.getByName("release")
            val isReleaseKeystorePresent = releaseSigning.storeFile != null && releaseSigning.storeFile!!.exists()
            val isStrictRelease = project.hasProperty("strictRelease") || System.getenv("STRICT_RELEASE") == "true" || System.getenv("CI") == "true"

            if (isStrictRelease && !isReleaseKeystorePresent) {
                throw GradleException("FATAL RELEASE BLOCKER: Release keystore is missing. Debug signing fallback is prohibited in CI/Production releases. Configure key.properties or provide STORE_FILE, KEY_ALIAS, and passwords.")
            }

            signingConfig = if (isReleaseKeystorePresent) {
                releaseSigning
            } else {
                logger.warn("WARNING: Release keystore not configured. Falling back to debug signing for local developer builds.")
                signingConfigs.getByName("debug")
            }
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
