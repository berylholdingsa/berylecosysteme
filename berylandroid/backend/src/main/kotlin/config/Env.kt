import java.io.File

object Env {
    private val dotenv: Map<String, String> = loadDotEnv()

    fun get(key: String): String? = System.getenv(key) ?: dotenv[key]

    fun getOrDefault(key: String, defaultValue: String): String = get(key) ?: defaultValue

    fun getRequired(key: String): String = get(key)
        ?: error("Missing required environment variable: $key")

    private fun loadDotEnv(): Map<String, String> {
        val candidates = listOf(File(".env"), File("backend/.env"))
        val file = candidates.firstOrNull { it.exists() && it.isFile } ?: return emptyMap()
        return file.readLines()
            .map { it.trim() }
            .filter { it.isNotEmpty() && !it.startsWith("#") && it.contains("=") }
            .associate { line ->
                val idx = line.indexOf('=')
                val key = line.substring(0, idx).trim()
                val value = line.substring(idx + 1).trim().trim('"')
                key to value
            }
    }
}
