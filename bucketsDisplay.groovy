import java.nio.file.*
import java.nio.charset.Charset
import java.util.zip.ZipOutputStream
import java.util.zip.ZipEntry

def host = "gdlfcft.endicott.ibm.com"
def user = "meghana"
def password = System.getenv("FTP_PASSWORD") ?: "B@NGAL0R"
def lftp = "/opt/homebrew/bin/lftp"
def bucketFile = "FETESTS.HTML"
def downloadDir = new File("download1")
downloadDir.mkdirs()

// Step 1: Download PXBUCKET.HTML
def bucketCmds = """
    lcd ${downloadDir.absolutePath}
    get ${bucketFile}
    bye
""".stripIndent().trim()

println "Downloading ${bucketFile}..."
def bucketDownloadCmd = "${lftp} -u ${user},${password} ${host} -e '${bucketCmds}'"
def bucketProcess = ["bash", "-c", bucketDownloadCmd].execute()
def bucketOut = new ByteArrayOutputStream()
def bucketErr = new ByteArrayOutputStream()
bucketProcess.waitForProcessOutput(bucketOut, bucketErr)

if (bucketErr.toString().trim()) {
    println "Error downloading ${bucketFile}:\n" + bucketErr.toString()
    System.exit(1)
}

// Step 2: Extract HTML links from PXBUCKET.HTML
def bucketContent = new File(downloadDir, bucketFile).getText("UTF-8")
def matcher = (bucketContent =~ /<a href=(\S+?\.HTML)>/)
def subFiles = matcher.collect { it[1].replaceAll(/[">]/, "") }.unique()

println "Sub HTML files to download:"
subFiles.each { println "- ${it}" }

// Step 3: Download each sub HTML file
subFiles.each { fileName ->
    def getCmds = """
        lcd ${downloadDir.absolutePath}
        get ${fileName}
        bye
    """.stripIndent().trim()

    println "Downloading ${fileName}..."
    def getCommand = "${lftp} -u ${user},${password} ${host} -e '${getCmds}'"
    def proc = ["bash", "-c", getCommand].execute()
    def out = new ByteArrayOutputStream()
    def err = new ByteArrayOutputStream()
    proc.waitForProcessOutput(out, err)

    if (err.toString().trim()) {
        println "Error downloading ${fileName}:\n" + err.toString()
    }
}

// Step 4: Create ZIP file
def zipFile = new File("PXBUCKET2.zip")
def zipStream = new ZipOutputStream(new FileOutputStream(zipFile))

downloadDir.eachFile { file ->
    zipStream.putNextEntry(new ZipEntry(file.name))
    zipStream.write(file.bytes)
    zipStream.closeEntry()
}
zipStream.close()

println "✅ ${bucketFile} created with ${subFiles.size() + 1} files."

