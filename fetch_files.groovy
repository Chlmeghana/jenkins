def fetchFtpFiles() {
    def host = "gdlfcft.endicott.ibm.com"
    def user = "meghana"
    def password = "B@NGAL0R" // For security, consider fetching this from environment variables.

    try {
        def command = "lftp -u ${user},${password} ${host} -e 'ls *.HATT; bye'"
        def process = ['bash', '-c', command].execute()
        def output = new StringBuffer()
        def error = new StringBuffer()
        process.waitForProcessOutput(output, error)

        if (error) {
            println "Error: $error"
            return []
        } else {
            def fileList = (output.toString() =~ /\b[A-Z0-9]+\.HATT\b/)*.toString()
            return fileList
        }

    } catch (Exception e) {
        println "Error: ${e.message}"
        return []
    }
}

def result = fetchFtpFiles()
println "$result"
