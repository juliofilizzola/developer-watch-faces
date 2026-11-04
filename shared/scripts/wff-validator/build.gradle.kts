plugins {
    kotlin("jvm") version "2.2.21"
    application
}

kotlin { jvmToolchain(17) }

dependencies {
    // Same XSD 1.1 stack as Google's reference validator (google/watchface).
    implementation("org.exist-db.thirdparty.xerces:xercesImpl:2.12.0:xml-schema-1.1")
    implementation("com.rackspace.eclipse.webtools.sourceediting:org.eclipse.wst.xml.xpath2.processor:2.1.100")
    implementation("edu.princeton.cup:java-cup:10k")
    implementation("xml-apis:xml-apis:1.4.01")
}

application {
    mainClass.set("dev.devtime.wff.ValidatorKt")
}
