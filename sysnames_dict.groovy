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
    def localFile = new File("${System.getProperty("user.home")}/goswat.tmp")

    if (localFile.exists()) {
        println "File '${localFile}' already exists. Using existing file."
    } else {
        println "Downloading 'goswat.sysnames' from FTP..."

def commands = """
    set xfer:clobber yes
    cd GPLSRV1:APARTEST.VMSWAT.BUILDS
    get goswat.sysnames -o ${localFile.absolutePath}
    bye
""".stripIndent().trim()


        try {
            def lftpCommand = "lftp -u ${user},${password} ${host} -e '${commands}'"
            def process = ["bash", "-c", lftpCommand].execute()
            def output = new StringBuffer()
            def error = new StringBuffer()
            process.waitForProcessOutput(output, error)

            if (error.toString().trim()) {
                return ["<ERROR> ${error.toString().trim()}"]
            }

        } catch (Exception e) {
            return ["<EXCEPTION> ${e.message}"]
        }
    }

    try {
        def bytes = Files.readAllBytes(localFile.toPath())
        println bytes
        def encodings = ["Cp500", "IBM1047", "Cp037"]
        for (encoding in encodings) {
            try {
                def decoded = new String(bytes, Charset.forName(encoding))
                println "Successfully decoded with $encoding"
                println "=" * 50
                def result = extractTableSection(decoded)
                println result
                println "=" * 50
                return result
            } catch (Exception e) {
                // Try next encoding
            }
        }

        return ["<ERROR> Could not decode using standard EBCDIC encodings."]
    } catch (Exception e) {
        return ["<EXCEPTION> ${e.message}"]
    }
}

// Entry point
def result = fetchFtpFiles()

