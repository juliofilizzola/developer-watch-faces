package dev.devtime.wff

import org.w3c.dom.Element
import org.xml.sax.ErrorHandler
import org.xml.sax.SAXParseException
import java.io.File
import javax.xml.parsers.DocumentBuilderFactory
import javax.xml.transform.stream.StreamSource
import javax.xml.validation.SchemaFactory
import kotlin.system.exitProcess

/**
 * Validates a Watch Face Format module:
 *  1. res/raw/watchface.xml against the official XSD 1.1 schema of the declared WFF version.
 *  2. Semantic checks the XSD cannot express: configuration/flavor cross references,
 *     referenced fonts/drawables exist, manifest declares hasCode=false and the format version.
 *
 * Usage: wff-validator <spec-dir> <module-dir> [<module-dir> ...]
 */
private const val MAX_USER_CONFIGURATIONS = 20
private const val MAX_COMPLICATION_SLOTS = 8

private val BUILT_IN_FONTS = setOf("SYNC_TO_DEVICE")

fun main(args: Array<String>) {
    if (args.size < 2) {
        System.err.println("usage: wff-validator <spec-dir> <module-dir>...")
        exitProcess(2)
    }
    val specDir = File(args[0])
    var failures = 0
    for (path in args.drop(1)) {
        val report = validateModule(specDir, File(path))
        report.print()
        if (report.errors.isNotEmpty()) failures++
    }
    exitProcess(if (failures == 0) 0 else 1)
}

class Report(val module: String) {
    val errors = mutableListOf<String>()
    val warnings = mutableListOf<String>()
    val info = mutableListOf<String>()

    fun print() {
        val status = if (errors.isEmpty()) "PASS" else "FAIL"
        println("[$status] $module")
        info.forEach { println("  info  $it") }
        warnings.forEach { println("  warn  $it") }
        errors.forEach { println("  error $it") }
    }
}

fun validateModule(specDir: File, module: File): Report {
    val report = Report(module.name)
    val res = File(module, "src/main/res")
    val manifest = File(module, "src/main/AndroidManifest.xml")
    val watchface = File(res, "raw/watchface.xml")

    if (!manifest.exists()) report.errors += "missing AndroidManifest.xml"
    if (!watchface.exists()) {
        report.errors += "missing res/raw/watchface.xml"
        return report
    }

    val version = if (manifest.exists()) checkManifest(manifest, report) else null
    val xsd = File(specDir, "${version ?: 2}/watchface.xsd")
    if (!xsd.exists()) {
        report.errors += "no schema for WFF version $version at ${xsd.path}"
        return report
    }
    checkSchema(xsd, watchface, report)
    checkSemantics(watchface, res, report)
    File(res, "xml/watch_face_info.xml").takeIf { !it.exists() }?.let {
        report.errors += "missing res/xml/watch_face_info.xml"
    }
    return report
}

private fun parse(file: File): Element {
    val dbf = DocumentBuilderFactory.newInstance()
    dbf.isNamespaceAware = true
    return dbf.newDocumentBuilder().parse(file).documentElement
}

private fun checkManifest(manifest: File, report: Report): Int? {
    val root = parse(manifest)
    val android = "http://schemas.android.com/apk/res/android"
    val app = root.getElementsByTagName("application").item(0) as? Element
    if (app == null) {
        report.errors += "manifest has no <application>"
        return null
    }
    if (app.getAttributeNS(android, "hasCode") != "false") {
        report.errors += "manifest <application> must declare android:hasCode=\"false\""
    }
    var version: Int? = null
    val props = app.getElementsByTagName("property")
    for (i in 0 until props.length) {
        val p = props.item(i) as Element
        if (p.getAttributeNS(android, "name") == "com.google.wear.watchface.format.version") {
            version = p.getAttributeNS(android, "value").toIntOrNull()
        }
    }
    if (version == null) report.errors += "manifest is missing property com.google.wear.watchface.format.version"
    else report.info += "WFF version $version"
    return version
}

private fun checkSchema(xsd: File, watchface: File, report: Report) {
    val factory = SchemaFactory.newInstance("http://www.w3.org/XML/XMLSchema/v1.1")
    val schema = factory.newSchema(xsd)
    val validator = schema.newValidator()
    validator.errorHandler = object : ErrorHandler {
        override fun warning(e: SAXParseException) {
            report.warnings += "xsd line ${e.lineNumber}: ${e.message}"
        }
        override fun error(e: SAXParseException) {
            report.errors += "xsd line ${e.lineNumber}: ${e.message}"
        }
        override fun fatalError(e: SAXParseException) {
            report.errors += "xsd line ${e.lineNumber}: ${e.message}"
        }
    }
    validator.validate(StreamSource(watchface))
}

private fun Element.childElements(): List<Element> {
    val out = mutableListOf<Element>()
    val nodes = childNodes
    for (i in 0 until nodes.length) (nodes.item(i) as? Element)?.let(out::add)
    return out
}

private fun Element.descendants(tag: String): List<Element> {
    val nodes = getElementsByTagName(tag)
    return (0 until nodes.length).map { nodes.item(it) as Element }
}

private fun resourceExists(res: File, name: String): Boolean =
    res.listFiles()?.filter { it.isDirectory && it.name.startsWith("drawable") }
        ?.any { dir -> dir.listFiles()?.any { it.nameWithoutExtension == name } == true } == true

private fun checkSemantics(watchface: File, res: File, report: Report) {
    val root = parse(watchface)
    val userConfigs = root.childElements().firstOrNull { it.tagName == "UserConfigurations" }

    // configuration id -> allowed option ids
    val declared = mutableMapOf<String, Set<String>>()
    val colorCounts = mutableMapOf<String, Int>()
    userConfigs?.childElements()?.forEach { cfg ->
        when (cfg.tagName) {
            "ListConfiguration" ->
                declared[cfg.getAttribute("id")] = cfg.childElements().map { it.getAttribute("id") }.toSet()
            "BooleanConfiguration" -> declared[cfg.getAttribute("id")] = setOf("TRUE", "FALSE")
            "ColorConfiguration" -> {
                val opts = cfg.childElements()
                declared[cfg.getAttribute("id")] = opts.map { it.getAttribute("id") }.toSet()
                colorCounts[cfg.getAttribute("id")] =
                    opts.minOfOrNull { it.getAttribute("colors").trim().split(Regex("\\s+")).size } ?: 0
            }
        }
        if (cfg.tagName != "Flavors" && !cfg.hasAttribute("defaultValue")) {
            report.errors += "configuration ${cfg.getAttribute("id")} has no defaultValue"
        }
    }
    val configCount = userConfigs?.childElements()?.size ?: 0
    report.info += "user configurations: $configCount/$MAX_USER_CONFIGURATIONS"
    if (configCount > MAX_USER_CONFIGURATIONS) report.errors += "more than $MAX_USER_CONFIGURATIONS user configurations"

    userConfigs?.childElements()?.filter { it.tagName != "Flavors" }?.forEach { cfg ->
        val id = cfg.getAttribute("id")
        val def = cfg.getAttribute("defaultValue")
        if (def !in (declared[id] ?: emptySet())) report.errors += "configuration $id: defaultValue '$def' is not an option"
    }

    // Scene usage of List/Boolean configurations must reference declared ids and options.
    val scene = root.childElements().first { it.tagName == "Scene" }
    for (tag in listOf("ListConfiguration", "BooleanConfiguration")) {
        for (use in scene.descendants(tag)) {
            val id = use.getAttribute("id")
            val allowed = declared[id]
            if (allowed == null) {
                report.errors += "scene uses undeclared configuration '$id'"
                continue
            }
            use.childElements().forEach { opt ->
                if (opt.getAttribute("id") !in allowed) report.errors += "scene option '${opt.getAttribute("id")}' not declared in '$id'"
            }
        }
    }

    // Flavors reference real configurations, options and slots.
    val slotIds = scene.descendants("ComplicationSlot").map { it.getAttribute("slotId") }.toSet()
    report.info += "complication slots: ${slotIds.size}/$MAX_COMPLICATION_SLOTS"
    val flavors = userConfigs?.descendants("Flavor") ?: emptyList()
    report.info += "flavors: ${flavors.size}"
    for (flavor in flavors) {
        for (c in flavor.childElements()) {
            when (c.tagName) {
                "Configuration" -> {
                    val allowed = declared[c.getAttribute("id")]
                    if (allowed == null) report.errors += "flavor ${flavor.getAttribute("id")}: unknown configuration ${c.getAttribute("id")}"
                    else if (c.getAttribute("optionId") !in allowed)
                        report.errors += "flavor ${flavor.getAttribute("id")}: '${c.getAttribute("optionId")}' is not an option of ${c.getAttribute("id")}"
                }
                "ComplicationSlot" -> if (c.getAttribute("slotId") !in slotIds)
                    report.errors += "flavor ${flavor.getAttribute("id")}: unknown slot ${c.getAttribute("slotId")}"
            }
        }
    }

    // [CONFIGURATION.id.N] color references point to an existing color index.
    val text = watchface.readText()
    Regex("""\[CONFIGURATION\.(\w+)\.(\d+)]""").findAll(text).map { it.groupValues }.toSet().forEach { (_, id, idx) ->
        val count = colorCounts[id]
        if (count == null) report.errors += "reference to undeclared color configuration '$id'"
        else if (idx.toInt() >= count) report.errors += "color reference $id.$idx exceeds the $count colors of each option"
    }

    // Fonts and image resources must be packaged.
    val fonts = (root.descendants("Font").map { it.getAttribute("family") }).toSet() - BUILT_IN_FONTS
    for (family in fonts) {
        val ok = File(res, "font").listFiles()?.any { it.nameWithoutExtension == family } == true
        if (!ok) report.errors += "font family '$family' not found in res/font"
    }
    val images = (root.descendants("Image") + root.descendants("InlineImage"))
        .map { it.getAttribute("resource") }.filter { !it.startsWith("[") }.toSet() +
        root.descendants("Character").map { it.getAttribute("resource") } +
        root.descendants("Word").map { it.getAttribute("resource") }
    for (img in images) if (!resourceExists(res, img)) report.errors += "drawable '$img' not found"

    // Every user-facing configuration label must be a string resource that exists.
    val strings = File(res, "values/strings.xml").takeIf { it.exists() }?.let { f ->
        parse(f).descendants("string").map { it.getAttribute("name") }.toSet()
    } ?: emptySet()
    val labels = mutableSetOf<String>()
    userConfigs?.let { uc ->
        listOf("ListConfiguration", "BooleanConfiguration", "ColorConfiguration", "ListOption", "ColorOption", "Flavor")
            .flatMap { uc.descendants(it) }
            .forEach { e -> e.getAttribute("displayName").takeIf { it.isNotEmpty() }?.let(labels::add) }
    }
    scene.descendants("ComplicationSlot").forEach { s -> s.getAttribute("displayName").takeIf { it.isNotEmpty() }?.let(labels::add) }
    labels.filter { it !in strings }.forEach { report.errors += "displayName '$it' has no string resource" }
    report.info += "string labels checked: ${labels.size}"

}
