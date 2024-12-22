// Function to handle connection to the server
export function onConnection(socket) {
  console.log("Connected to Server.");
  socket.emit("connected"); // Notify the server of the connection

  const connectionDiv = document.getElementById("connection");
  connectionDiv.innerHTML = ""; // Clear existing content

  const pre = document.createElement("pre"); // Create a <pre> element for formatted text
  pre.classList.add("text-grey-color", "text-sm", "inline");

  const img = document.createElement("img"); // Create an image element for the checkmark
  img.classList.add("mr-5", "w-[20px]", "inline");
  img.src = "static/img/check_green_circle.svg"; // Set the image source

  pre.appendChild(img); // Append the image to the <pre>
  pre.appendChild(document.createTextNode(window.location.origin)); // Append the current origin
  connectionDiv.appendChild(pre); // Add the <pre> to the connectionDiv
}

// Function to handle disconnection from the server
export function onDisconnect() {
  console.log("Disconnected from Server.");
  const connectionDiv = document.getElementById("connection");
  connectionDiv.innerHTML = ""; // Clear existing content

  const pre = document.createElement("pre"); // Create a <pre> for disconnection message
  pre.classList.add("text-grey-color", "text-sm", "inline");

  const img = document.createElement("img"); // Create an image for the cross mark
  img.classList.add("inline");
  img.src = "static/img/cross_red_circle.svg"; // Set the image source

  pre.appendChild(img); // Append the image to the <pre>
  connectionDiv.appendChild(pre); // Add the <pre> to the connectionDiv
}

export function onMenu(menu, type, socket) {
  const typeNav = document.getElementById("nav-" + type);
  typeNav.innerHTML = ""; // Clear the content of the container

  // Add menu title
  const title = createTitle(menu.name);
  typeNav.appendChild(title);

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
        const inputParams = createInput("number");
        inputContainer.appendChild(button);
        inputContainer.appendChild(inputParams);
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
    // Add click event listener
    console.log(`${type}_cmd`, cmd);
    if (type === "tool") {
      socket.emit(`${type}_cmd`, cmd); // Emit command for tools
    } else {
      socket.emit(`${type}_cmd`, 1, cmd); // Emit command for other types
    }
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
