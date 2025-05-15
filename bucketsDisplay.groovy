import java.nio.file.*
import java.nio.charset.Charset
import java.util.zip.ZipOutputStream
import java.util.zip.ZipEntry

def host = "gdlfcft.endicott.ibm.com"
def user = "meghana"
def password = System.getenv("FTP_PASSWORD") ?: "B@NGAL0R"
def lftp = "/opt/homebrew/bin/lftp"
def bucketFile = "PXBUCKET.HTML"
def downloadDir = new File("download1")
downloadDir.mkdirs()

// Step 1: Download UHBUCKET.HTML if not already downloaded
def bucketTarget = new File(downloadDir, bucketFile)
if (!bucketTarget.exists()) {
    def bucketCmds = """
        lcd ${downloadDir.absolutePath}
        set xfer:clobber on
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
} else {
    println "${bucketFile} already exists, skipping download."
}

// Step 2: Extract HTML links from UHBUCKET.HTML
def bucketContent = bucketTarget.getText("UTF-8")
def matcher = (bucketContent =~ /<a href=(\S+?\.HTML)>/)
def subFiles = matcher.collect { it[1].replaceAll(/[">]/, "") }.unique()

println "Sub HTML files to download:"
subFiles.each { println "- ${it}" }

// Step 3: Download each sub HTML file if not already present
subFiles.each { fileName ->
    def targetFile = new File(downloadDir, fileName)
    if (targetFile.exists()) {
        println "${fileName} already exists, skipping download."
        return
    }

    def getCmds = """
        lcd ${downloadDir.absolutePath}
        set xfer:clobber on
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
def zipFile = new File("Output.zip")
def zipStream = new ZipOutputStream(new FileOutputStream(zipFile))

downloadDir.eachFile { file ->
    zipStream.putNextEntry(new ZipEntry(file.name))
    zipStream.write(file.bytes)
    zipStream.closeEntry()
}
zipStream.close()

println "✅ Output.zip created with ${downloadDir.listFiles().size()} files."
