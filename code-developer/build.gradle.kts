import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
}

// Release signing is optional: create keystore.properties at the repo root
// (see docs/PUBLISHING.md). Without it, bundleRelease produces an unsigned AAB.
val keystoreProps = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

android {
    enableKotlin = false
    namespace = "dev.devtime.watchface.code"
    compileSdk = 34

    defaultConfig {
        applicationId = "dev.devtime.watchface.code"
        // WFF v2 (Flavors, weather, heart rate source) requires Wear OS 5 = API 34.
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
    }

    if (keystoreProps.isNotEmpty()) {
        signingConfigs {
            create("upload") {
                storeFile = rootProject.file(keystoreProps.getProperty("storeFile"))
                storePassword = keystoreProps.getProperty("storePassword")
                keyAlias = keystoreProps.getProperty("keyAlias")
                keyPassword = keystoreProps.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        // R8 strips the generated R classes: bundletool rejects watch faces (minSdk >= 33) with dex files.
        debug {
            isMinifyEnabled = true
        }
        release {
            isMinifyEnabled = true
            // Resources are referenced by name from watchface.xml: never shrink them.
            isShrinkResources = false
            if (keystoreProps.isNotEmpty()) signingConfig = signingConfigs.getByName("upload")
        }
    }
}
