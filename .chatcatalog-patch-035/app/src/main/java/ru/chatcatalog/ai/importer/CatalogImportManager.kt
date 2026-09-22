package ru.chatcatalog.ai.importer

import android.content.ContentResolver
import android.net.Uri
import android.provider.OpenableColumns
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.Locale
import java.util.zip.ZipInputStream

class CatalogImportManager(
    private val contentResolver: ContentResolver
) {
    suspend fun import(uri: Uri): ImportedCatalogDocument = withContext(Dispatchers.IO) {
        val fileName = queryDisplayName(uri) ?: "catalog"
        val lower = fileName.lowercase(Locale.ROOT)
        val mime = contentResolver.getType(uri).orEmpty().lowercase(Locale.ROOT)
        val markdown = when {
            lower.endsWith(".zip") || mime.contains("zip") -> importZip(uri)
            lower.endsWith(".md") || lower.endsWith(".markdown") || mime.contains("markdown") || mime == "text/plain" -> readText(uri)
            lower.endsWith(".json") || mime.contains("json") -> importJson(readText(uri))
            else -> runCatching { importZip(uri) }.getOrElse { readText(uri) }
        }.trim().removePrefix("\uFEFF").trim()

        require(markdown.isNotBlank()) { "Импортированный каталог пуст" }
        require(markdown.length <= MAX_TEXT_CHARS) {
            "Каталог слишком большой: ${markdown.length} символов. Максимум $MAX_TEXT_CHARS"
        }
        validateReadyCatalog(markdown, fileName)

        val title = detectTitle(markdown).ifBlank { fileName.substringBeforeLast('.') }
        val sections = SECTION_RE.findAll(markdown).count().coerceAtLeast(1)
        val refs = SOURCE_RE.findAll(markdown).map { it.value.lowercase(Locale.ROOT) }.distinct().count()
        ImportedCatalogDocument(
            title = title,
            sourceFileName = fileName,
            markdown = markdown,
            sectionCount = sections,
            sourceReferenceCount = refs,
            importedAt = System.currentTimeMillis()
        )
    }

    private fun importZip(uri: Uri): String {
        val candidates = linkedMapOf<String, String>()
        var rawChatArchive = false
        contentResolver.openInputStream(uri)?.use { input ->
            ZipInputStream(input.buffered()).use { zip ->
                while (true) {
                    val entry = zip.nextEntry ?: break
                    if (entry.isDirectory) continue
                    val name = entry.name.substringAfterLast('/').lowercase(Locale.ROOT)

                    if (name == "messages.md" || name == "messages.jsonl") {
                        rawChatArchive = true
                    }

                    val priority = when {
                        name == "catalog_current.md" -> "0"
                        name == "catalog.md" -> "1"
                        name == "catalog_structured.json" -> "2"
                        name == "catalog.json" -> "3"
                        name.startsWith("catalog_") && name.endsWith(".md") -> "4:$name"
                        name.startsWith("catalog_") && name.endsWith(".json") -> "5:$name"
                        else -> null
                    } ?: continue

                    val bytes = readLimited(zip, MAX_ZIP_ENTRY_BYTES)
                    val text = bytes.toString(Charsets.UTF_8).removePrefix("\uFEFF")
                    if (name.endsWith(".json")) {
                        runCatching { importJson(text) }.getOrNull()?.let { candidates[priority] = it }
                    } else if (text.isNotBlank()) {
                        candidates[priority] = text
                    }
                }
            }
        } ?: error("Не удалось открыть файл")

        candidates.toSortedMap().values.firstOrNull()?.let { return it }

        if (rawChatArchive) {
            error(
                "Вы выбрали СЫРОЙ AI-архив чата (messages.md/messages.jsonl), а не готовый каталог. " +
                    "Этот ZIP нужно сначала обработать в ChatGPT. Для меню бота импортируйте полученный " +
                    "ChatCatalog_*_каталог_*.zip или файл CATALOG_CURRENT.md."
            )
        }

        error("В ZIP не найден готовый каталог: нужен CATALOG_CURRENT.md или CATALOG_STRUCTURED.json")
    }

    private fun importJson(text: String): String {
        val root = JSONObject(text)
        listOf("catalog_markdown", "markdown", "catalog").forEach { key ->
            val value = root.optString(key, "")
            if (value.isNotBlank()) return value
        }

        val sections = root.optJSONArray("sections")
        if (sections != null && sections.length() > 0) {
            return renderSectionsJson(root.optString("title", "Импортированный каталог"), sections)
        }

        error("JSON содержит данные архива, но не готовый каталог. Импортируйте ZIP каталога или CATALOG_CURRENT.md")
    }

    private fun renderSectionsJson(title: String, sections: JSONArray): String = buildString {
        appendLine("# $title")
        for (i in 0 until sections.length()) {
            val section = sections.optJSONObject(i) ?: continue
            val sectionTitle = section.optString("title", "Раздел ${i + 1}")
            appendLine()
            appendLine("## $sectionTitle")
            val body = section.optString("body", "")
            if (body.isNotBlank()) appendLine(body)
            val items = section.optJSONArray("items") ?: continue
            for (j in 0 until items.length()) {
                val item = items.opt(j)
                when (item) {
                    is String -> appendLine("- $item")
                    is JSONObject -> {
                        val itemTitle = item.optString("title", "")
                        val itemBody = item.optString("body", item.optString("text", ""))
                        append("- ")
                        if (itemTitle.isNotBlank()) append("**$itemTitle**")
                        if (itemTitle.isNotBlank() && itemBody.isNotBlank()) append(": ")
                        appendLine(itemBody)
                    }
                }
            }
        }
    }

    private fun validateReadyCatalog(markdown: String, fileName: String) {
        val title = markdown.lineSequence()
            .map { it.trim() }
            .firstOrNull { it.startsWith("# ") }
            ?.removePrefix("# ")
            ?.trim()
            .orEmpty()

        val timestampSections = RAW_MESSAGE_SECTION_RE.findAll(markdown).count()
        val rawExport = title.startsWith("Telegram chat export:", ignoreCase = true) ||
            (timestampSections >= 3 && RAW_MESSAGE_META_RE.containsMatchIn(markdown))

        require(!rawExport) {
            "Это сырой экспорт сообщений Telegram, а не готовый каталог. " +
                "Не публикуйте messages.md в бот. Отправьте AI-архив в ChatGPT и затем импортируйте " +
                "готовый ChatCatalog_*_каталог_*.zip или CATALOG_CURRENT.md."
        }

        val sections = SECTION_RE.findAll(markdown).count()
        require(sections > 0) {
            "Файл $fileName не похож на готовый каталог: не найдены смысловые разделы '## ...'. " +
                "Импортируйте CATALOG_CURRENT.md."
        }
    }

    private fun readText(uri: Uri): String {
        val bytes = contentResolver.openInputStream(uri)?.use { readLimited(it, MAX_ZIP_ENTRY_BYTES) }
            ?: error("Не удалось открыть файл")
        return bytes.toString(Charsets.UTF_8)
    }

    private fun queryDisplayName(uri: Uri): String? = runCatching {
        contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (!cursor.moveToFirst()) return@use null
            cursor.getString(0)
        }
    }.getOrNull()

    private fun detectTitle(markdown: String): String {
        val firstHeading = markdown.lineSequence()
            .map { it.trim() }
            .firstOrNull { it.startsWith("# ") }
            ?.removePrefix("# ")
            ?.trim()
            .orEmpty()
        return firstHeading
            .replace(Regex("(?i)^каталог\\s+(знаний\\s+)?чата\\s*"), "")
            .trim(' ', '«', '»', '"')
    }

    private fun readLimited(input: java.io.InputStream, maxBytes: Int): ByteArray {
        val out = ByteArrayOutputStream()
        val buffer = ByteArray(8192)
        var total = 0
        while (true) {
            val read = input.read(buffer)
            if (read < 0) break
            total += read
            if (total > maxBytes) throw IOException("Текстовый файл каталога превышает ${maxBytes / 1024 / 1024} МБ")
            out.write(buffer, 0, read)
        }
        return out.toByteArray()
    }

    companion object {
        private const val MAX_ZIP_ENTRY_BYTES = 12 * 1024 * 1024
        private const val MAX_TEXT_CHARS = 8_000_000
        private val SECTION_RE = Regex("(?m)^##\\s+")
        private val SOURCE_RE = Regex("(?i)\\bmsg\\s+\\d+\\b")
        private val RAW_MESSAGE_SECTION_RE = Regex(
            "(?m)^##\\s+\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2}(?:\\s+[+-]\\d{2}:\\d{2})?\\s+—\\s+"
        )
        private val RAW_MESSAGE_META_RE = Regex("(?m)^\`message_id=\\d+\`\\s+·\\s+\`type=")
    }
}

data class ImportedCatalogDocument(
    val title: String,
    val sourceFileName: String,
    val markdown: String,
    val sectionCount: Int,
    val sourceReferenceCount: Int,
    val importedAt: Long
)
