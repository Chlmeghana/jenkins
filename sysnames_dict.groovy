import java.nio.file.*
import java.nio.charset.Charset

def extractTableSection(String content) {
    def startLine = "-------  -------- -------- ----------- ------- -------- --------- ------- -------- ------ ------- ----------------------------"
    int index = content.indexOf(startLine)
    if (index == -1) {
        println "Header not found!"
        return []
    }

    def cleaned = content.substring(index).replaceAll('-', '').trim()
    def fields = cleaned.split(/\s+/)

    def result = [:]
    int i = 0
    while (i < fields.size()) {
        def systemName = fields[i]
        def domainName

        if (fields[i + 1] == "NONE") {
            domainName = "NONE"
            i += 11
        } else {
            domainName = fields[i + 11]
            i += 12
        }
        result[systemName] = domainName
    }

    return result.keySet().toList()
}

def fetchFtpFiles() {
    def host = "gdlvm7.pok.ibm.com"
    def user = "meghana"
    def password = System.getenv("FTP_PASSWORD") ?: "Meghana@2003"
    def localFile = new File("goswat.tmp")

    try {
        if (!localFile.exists()) {
            println "Downloading 'goswat.sysnames' from FTP..."

            def commands = """
                cd GPLSRV1:APARTEST.VMSWAT.BUILDS
                get goswat.sysnames -o goswat.tmp
                bye
            """.stripIndent().trim()

            // Construct full command as pure String
            def fullCommand = "lftp -u ${user},${password} ${host} -e \"${commands}\""
            def process = new ProcessBuilder(["bash", "-c", fullCommand] as String[])
                .redirectErrorStream(true)
                .start()

            process.inputStream.withReader { reader ->
                reader.eachLine { println it }
            }

            def exitCode = process.waitFor()
            if (exitCode != 0) {
                throw new RuntimeException("FTP download failed with exit code ${exitCode}")
            }
        } else {
            println "File 'goswat.tmp' already exists. Using existing file."
        }

        // Read binary content
        def bytes = Files.readAllBytes(Paths.get("goswat.tmp"))

        // Try decoding with EBCDIC encodings
        def encodings = ["Cp500", "IBM1047", "Cp037"]
        boolean success = false

        for (encoding in encodings) {
            try {
                def decoded = new String(bytes, Charset.forName(encoding))
                println "Successfully decoded with $encoding"
                println "=" * 50
                def result = extractTableSection(decoded)
                println result
                println "=" * 50
                success = true
                break
            } catch (Exception e) {
                // Continue trying next encoding
            }
        }

        if (!success) {
            println "Could not decode using standard EBCDIC encodings."
        }

    } catch (Exception e) {
        println "Error: ${e.message}"
        e.printStackTrace()
    }
}

// Entry point
fetchFtpFiles()
