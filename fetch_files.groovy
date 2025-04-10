def fetchFtpFiles() {
    def host = "gdlfcft.endicott.ibm.com"
    def user = System.getenv("FTP_USER") ?: "meghana"
    def password = System.getenv("FTP_PASS") ?: "B@NGAL0R"
    try {
        def command = "lftp -u ${user},${password} ${host} -e 'ls *.HATT; bye'"
        def process = ['bash', '-c', command].execute()
        def output = new StringBuffer()
        def error = new StringBuffer()
        process.waitForProcessOutput(output, error)
        if (error.toString().trim()) {
            println "Error: $error"
            return ""
        } else {
            def fileList = (output.toString() =~ /[A-Z0-9]+\.HATT/).findAll()
            def fileListStr = fileList.join(",")
            println "FILE_LIST=${fileListStr}" // For Jenkins to pick it up
            return fileListStr
        }
    } catch (Exception e) {
        println "Exception: ${e.message}"
        return ""
    }
}
def result = fetchFtpFiles()
println "Fetched files: $result"
