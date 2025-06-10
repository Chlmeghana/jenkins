/* import java.nio.file.*
import java.nio.charset.Charset
import java.util.zip.ZipOutputStream
import java.util.zip.ZipEntry

def host = "gdlfcft.endicott.ibm.com"
def user = "meghana"
def password = System.getenv("FTP_PASSWORD") ?: "B@NGAL0R"
def lftp = "/opt/homebrew/bin/lftp"
def bucketFile = "FETESTS.HTML"
def downloadDir = new File("download1")
if (downloadDir.exists()) {
    downloadDir.eachFile { it.delete() }
} else {
    downloadDir.mkdirs()
}

// Step 1: Download file.HTML
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

// Step 2: Extract HTML links from file.HTML
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
def zipFile = new File("Output.zip")
def zipStream = new ZipOutputStream(new FileOutputStream(zipFile))

downloadDir.eachFile { file ->
    zipStream.putNextEntry(new ZipEntry(file.name))
    zipStream.write(file.bytes)
    zipStream.closeEntry()
}
zipStream.close() */


import java.nio.file.*
import java.util.zip.ZipOutputStream
import java.util.zip.ZipEntry

def host = "gdlfcft.endicott.ibm.com"
def user = "meghana"
def password = System.getenv("FTP_PASSWORD") ?: "B@NGAL0R"
def lftp = "/opt/homebrew/bin/lftp"
def downloadDir = new File("Output")

// Prompt for file name
print "Enter the name of the HTML file to download (e.g., FETESTS.HTML): "
def bucketFile = System.console().readLine()?.trim()

if (!bucketFile || !bucketFile.toUpperCase().endsWith(".HTML")) {
    println "❌ Invalid file name."
    System.exit(1)
}

// Prepare download directory
if (downloadDir.exists()) {
    downloadDir.eachFile { it.delete() }
} else {
    downloadDir.mkdirs()
}

// Function to download a file via FTP
def downloadFile = { String fileName, File dir ->
    def cmds = """
        set xfer:clobber yes;
        lcd ${dir.absolutePath}
        get ${fileName}
        bye
    """.stripIndent().trim()

    println "Downloading ${fileName}..."
    def command = "${lftp} -u ${user},${password} ${host} -e '${cmds}'"
    def proc = ["bash", "-c", command].execute()
    def out = new ByteArrayOutputStream()
    def err = new ByteArrayOutputStream()
    proc.waitForProcessOutput(out, err)

    if (err.toString().trim()) {
        println "⚠️ Error downloading ${fileName}:\n" + err.toString()
        return false
    }
    return true
}

// Recursive function to process bucket files
def processBucketFile
processBucketFile = { String fileName, File dir, Set<String> processedFiles = [] as Set ->
    if (fileName in processedFiles) return []
    
    processedFiles << fileName
    def allFiles = [fileName]
    
    if (!downloadFile(fileName, dir)) return allFiles
    
    def content = new File(dir, fileName).getText("UTF-8")
    def matcher = (content =~ /<a href=(\S+?\.HTML)>/)
    def subFiles = matcher.collect { it[1].replaceAll(/[">]/, "") }.unique()
    
    // Check for bucket files (with "BUCKET *" in the link text)
    def bucketMatcher = (content =~ /<li><a href=(\S+?\.HTML)>.*BUCKET \*<\/a>/)
    def bucketFiles = bucketMatcher.collect { it[1].replaceAll(/[">]/, "") }.unique()
    
    println "\nFound in ${fileName}:"
    subFiles.each { println "- ${it}" + (it in bucketFiles ? " (BUCKET)" : "") }
    
    // Process all sub-files
    subFiles.each { subFile ->
        if (!(subFile in processedFiles)) {
            allFiles.addAll(processBucketFile(subFile, dir, processedFiles))
        }
    }
    
    return allFiles.unique()
}

// Main execution
println "\nStarting download process..."
def allFiles = processBucketFile(bucketFile, downloadDir)

println "\nDownloaded files:"
allFiles.each { println "- ${it}" }

// Create ZIP file
def zipFile = new File("OUTPUT.zip")
if (zipFile.exists()) zipFile.delete()

def zipStream = new ZipOutputStream(new FileOutputStream(zipFile))
downloadDir.eachFile { file ->
    if (file.name in allFiles) {
        zipStream.putNextEntry(new ZipEntry(file.name))
        zipStream.write(file.bytes)
        zipStream.closeEntry()
    }
}
zipStream.close()

println "\n✅ ZIP file 'OUTPUT.zip' created with ${allFiles.size()} files."

println "✅ ${bucketFile} created with ${subFiles.size() + 1} files."

