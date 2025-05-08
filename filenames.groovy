def fetchFtpFiles() {
    def host = "gdlfcft.endicott.ibm.com"
    def user = "meghana"
    def password = "B@NGAL0R"

    def commands = """
        cd SERVCT:TOOLS.CHUG
        ls *.HATT
        ls *.BUCKET
        cd SERVCT:TOOLS.CHUG.HATT
        ls *.HATT
        ls *.BUCKET
        bye
    """.stripIndent()

    def processBuilder = new ProcessBuilder("lftp", "-u", "$user,$password", host, "-e", commands)
    def process = processBuilder.start()
    def output = process.inputStream.text
    def errorOutput = process.errorStream.text

    if (process.waitFor() != 0) {
        println "Error executing FTP command:"
        println errorOutput
        return
    }

    // Extract filenames (last field of each non-empty line)
    def lines = output.split("\n")
    def filenames = lines.findAll { it && !it.startsWith('cd ok') }
                          .collect { it.split()[-1] }

    println filenames
}

// Entry point
fetchFtpFiles()
