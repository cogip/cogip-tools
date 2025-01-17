export function onConnection(socket) {
  console.log("Connected to Server.");
  socket.emit("connected");

  const connectionDiv = document.getElementById("connection");
  updateConnectionStatus(
    connectionDiv,
    "check_green_circle",
    window.location.origin
  );
}

export function onDisconnect() {
  console.log("Disconnected from Server.");
  const connectionDiv = document.getElementById("connection");
  updateConnectionStatus(connectionDiv, "cross_red_circle");
}

function updateConnectionStatus(container, icon, text = "") {
  container.innerHTML = ""; // Clear existing content

  const pre = document.createElement("pre");
  pre.classList.add("text-grey-color", "text-sm", "inline");

  const img = document.createElement("img");
  img.classList.add("inline", "mr-5", "w-[20px]");
  img.src = `static/img/${icon}.svg`;

  pre.appendChild(img);
  if (text) pre.appendChild(document.createTextNode(text));
  container.appendChild(pre);
}

// disconnected websocket
function disconnectWebSocket(socket) {
  if (socket) {
    console.log("Closing WebSocket...");
    socket.close(); // close connection
    socket = null; // clear variable
  } else {
    console.log("WebSocket is already closed or not initialized.");
  }
}

export function setupTabEventListener(
  tabId,
  panelId,
  socket,
  iframeUrlCallback
) {
  document.getElementById(tabId)?.addEventListener("click", function (e) {
    // Disconnect the WebSocket
    disconnectWebSocket(socket);

    // Retrieve the current tab's identifier
    const tabIdMatch = e.target.getAttribute("id").match(/robot(\d+)-tab/);
    const robotId = tabIdMatch ? tabIdMatch[1] : null;

    // Activate the newly selected tab
    document.querySelectorAll('[role="tab"]').forEach((tab) => {
      tab.classList.toggle("text-red-cogip", tab === e.target);
      tab.classList.toggle("border-red-cogip", tab === e.target);
      tab.classList.toggle("text-gray-600", tab !== e.target);
      tab.classList.toggle("border-transparent", tab !== e.target);
    });

    // Hide all panels and reset their iframes
    document.querySelectorAll('[role="tabpanel"]').forEach((pane) => {
      const otherPaneId = pane.id.match(/robot(\d+)/)?.[1];
      if (otherPaneId) {
        document
          .getElementById(`robot${otherPaneId}-iframe`)
          ?.removeAttribute("src");
      }
      pane.classList.toggle("hidden", pane.id !== panelId); // Hide all panels
    });

    // If an iframe is needed, update its source
    if (iframeUrlCallback && robotId) {
      const iframe = document.getElementById(`robot${robotId}-iframe`);
      iframe.src = iframeUrlCallback(robotId);
    } else {
      // Reopen the socket if needed
      socket.open();
    }
  });
}

export function onMenu(menu, type, socket) {
  const typeNav = document.getElementById(`nav-${type}`);
  typeNav.innerHTML = ""; // Clear the content of the container

  // Add menu title
  typeNav.appendChild(createTitle(menu.name));

  // Create the container for the buttons
  const buttonContainer = document.createElement("div");
  buttonContainer.classList.add("max-h-[72vh]", "overflow-y-auto");

  // Separate "Exit Menu" from other entries
  const exitMenuEntry = menu.entries.find(
    (entry) => entry.desc === "Exit Menu"
  );
  let otherEntries = menu.entries.filter((entry) => entry.desc !== "Exit Menu");

  // Sort other entries alphabetically only if "Exit Menu" is not present
  if (!exitMenuEntry) {
    otherEntries = otherEntries.sort((a, b) => a.desc.localeCompare(b.desc));
  }

  // Combine "Exit Menu" first, followed by the other entries
  const entriesToDisplay = exitMenuEntry
    ? [exitMenuEntry, ...otherEntries]
    : otherEntries;

  // Add all sorted menu buttons
  entriesToDisplay.forEach((entry) => {
    if (!entry.cmd.startsWith("_")) {
      const button = createButton(entry.desc, entry.cmd, type, socket);

      if (entry.desc.includes("<")) {
        // Add an input field if required
        const inputContainer = document.createElement("div");
        inputContainer.appendChild(button);
        inputContainer.appendChild(createInput("number"));
        buttonContainer.appendChild(inputContainer);
      } else {
        buttonContainer.appendChild(button);
        buttonContainer.appendChild(document.createElement("br"));
      }
    }
  });

  typeNav.appendChild(buttonContainer); // Add button container to navigation
}

// Function to create the menu title
function createTitle(name) {
  const h1 = document.createElement("h1"); // Create an <h1> element for the title
  h1.classList.add("small", "text-grey-color");
  h1.textContent = name; // Set the title text
  return h1;
}

// Function to create a menu button
function createButton(description, cmd, type, socket) {
  const button = document.createElement("button"); // Create a button element
  button.type = "button";
  button.classList.add(
    "px-2",
    "py-2",
    "mb-2",
    "bg-zinc-800",
    "text-grey-color",
    "rounded",
    "hover:bg-gray-600",
    "focus:outline-none"
  );
  button.textContent = description; // Set button text

  button.addEventListener("click", () => {
    console.log(`${type}_cmd`, cmd);
    socket.emit(`${type}_cmd`, type === "tool" ? cmd : [1, cmd]);
  });

  return button; // Return the created button
}

// Function to create an input field
function createInput(inputType) {
  const input = document.createElement("input"); // Create an input element
  input.classList.add("use-keyboard-input"); // Add class for keyboard input
  input.type = inputType; // Set input type
  return input; // Return the created input
}
