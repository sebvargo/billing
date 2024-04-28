Dropzone.autoDiscover = false;
document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("file-dropzone2")
    .addEventListener("submit", function (event) {
      event.preventDefault(); // Prevent the default form submission
    });
});

const tkn_for_dropzone = document.getElementById("tkn").value;
let myDropzone = new Dropzone("#file-dropzone2", {
  paramName: "file",
  url: "/documents",
  maxFilesize: 50,
  acceptedFiles: `application/pdf`,
  headers: {
    Authorization: "Bearer " + tkn_for_dropzone,
  },
  init: function () {
    this.on("success", function (file, response) {
      console.log("Response received");
      gridInstance.forceRender();
      setTimeout(() => {
      if (response.document_id) {
        let documentId = response.document_id;
        let progress = parseInt(response.progress);
        console.log(`Document ID: ${documentId}`);
        let progressSpan = document.getElementById(`progress-span-${documentId}`);
        if (progressSpan) {progressSpan.innerHTML = progress + "%";}
        let progressBar = document.getElementById(`progress-bar-${documentId}`);
        if (progressBar) {
          progressBar.style.width = progress + "%";
          if (progress >= 100) {
            progressBar.classList.remove("bg-info");
            progressBar.classList.add("progress-bar", "bg-success");
            }
          }
      } else {
        console.error("No document ID returned from the server.");
      }

      if (file.previewElement) {
        file.previewElement.classList.add("dz-success"); // Add success class to the preview element
      }
    }, 500);
    });
  },
});
myDropzone.on("addedfile", (file) => {
  console.log(`File added: ${file.name}`);
});