let streaming = null; // Hold the streaming element globally

const cameraDom = document.getElementById("cameraModal");
const urlParams = new URLSearchParams(window.location.search);

window.modalCamera = function () {
  if (cameraDom.style.display !== "flex") {
    // Create the streaming element only if it doesn't exist
    if (!streaming) {
      streaming = document.createElement("img");
      streaming.setAttribute("id", "streaming");
      streaming.style.width = "100%";
      streaming.loading = "lazy";

      const hostname = window.location.hostname;
      const port = window.location.port
        ? parseInt(window.location.port) + 20
        : "your_default_port";
      streaming.src = `http://${hostname}:${port}/`;

      // Error handling for image loading
      streaming.onerror = function () {
        console.error("Error loading the stream.");
        // Optionally show an error message to the user
      };

      document.getElementById("displayFlux").appendChild(streaming);
    }

    cameraDom.classList.remove("hidden");
    cameraDom.style.display = "flex";
  }
};

window.closeModal = function (modalId) {
  const modal = document.getElementById(modalId);
  modal.classList.add("hidden");
  modal.style.display = "none";

  // Reset streaming only if it exists
  if (streaming) {
    streaming.src = ""; // Reset the source
    // Optionally remove the streaming element if not needed
    // streaming.remove();
    streaming = null; // Reset streaming reference
  }
};
