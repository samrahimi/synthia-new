async function requestFileSystemPermission() {
    const handle = await window.showDirectoryPicker();
    return handle
  }

  // Save the current DOM state to index2.html
  async function saveDOMToFile(filename) {
    const synthDir = await requestFileSystemPermission();
    const fileHandle = await synthDir.getFileHandle(filename, { create: true });
    const writableStream = await fileHandle.createWritable();
    await writableStream.write(new Blob([document.documentElement.outerHTML], { type: "text/html" }));
    await writableStream.close();
    console.log("File saved successfully");
  }

  // Add click event to the save button to call saveDOMToFile()
  $("#saveButton").on("click", function () {
    filename=prompt("Save As...", "new.html")
    saveDOMToFile();
  });
