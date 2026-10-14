plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }

fun environment(name: String, fallback: String = "") = providers.environmentVariable(name).orElse(fallback).get()
fun quoted(value: String): String = "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
val publicKey = environment("OFFLINE_PUBLIC_KEY")
val contentBase = environment("OFFLINE_CONTENT_BASE", "https://kiansheik.io/nhe-enga/")
val releaseRequested = gradle.startParameter.taskNames.any { it.contains("Release", ignoreCase = true) }
if (releaseRequested) {
    require(publicKey.isNotBlank()) { "OFFLINE_PUBLIC_KEY (base64 X.509 RSA public key) is required for release" }
    require(contentBase.startsWith("https://")) { "Release content must use HTTPS" }
    for (name in listOf("APK_KEYSTORE", "APK_STORE_PASSWORD", "APK_KEY_ALIAS", "APK_KEY_PASSWORD")) {
        require(environment(name).isNotBlank()) { "$name is required; never commit signing secrets" }
    }
}
android {
    namespace = "io.kiansheik.nheenga"
    compileSdk = 35
    defaultConfig {
        applicationId = "io.kiansheik.nheenga"
        minSdk = 23
        targetSdk = 35
        versionCode = environment("APK_VERSION_CODE", "1").toInt()
        versionName = environment("APK_VERSION_NAME", "0.1.0")
        buildConfigField("String", "CONTENT_BASE", quoted(contentBase))
        buildConfigField("String", "CONTENT_PUBLIC_KEY", quoted(publicKey))
        buildConfigField("int", "SHELL_PROTOCOL", "1")
        manifestPlaceholders["cleartext"] = "false"
    }
    signingConfigs {
        create("release") {
            if (releaseRequested) {
                storeFile = file(environment("APK_KEYSTORE"))
                storePassword = environment("APK_STORE_PASSWORD")
                keyAlias = environment("APK_KEY_ALIAS")
                keyPassword = environment("APK_KEY_PASSWORD")
            }
        }
    }
    buildTypes {
        debug { applicationIdSuffix = ".debug"; manifestPlaceholders["cleartext"] = "true" }
        release {
            isMinifyEnabled = true; isShrinkResources = true
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
        }
    }
    buildFeatures { buildConfig = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.webkit:webkit:1.14.0")
    implementation("androidx.work:work-runtime-ktx:2.10.5")
    testImplementation("junit:junit:4.13.2")
}
