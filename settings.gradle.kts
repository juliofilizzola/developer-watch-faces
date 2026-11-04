pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "developer-watch-faces"

// Each watch face is an independent, resource-only application module
// (own applicationId, own resources, own APK/AAB). No module depends on another.
include(":json-developer")
include(":code-developer")
include(":matrix-developer")
