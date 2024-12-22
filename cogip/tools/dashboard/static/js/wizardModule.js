let socket = null;
let message = null;

export function openWizardModal(msg, send_socket) {
  socket = send_socket;
  message = msg;

  const wizardName = document.getElementById("wizardName");
  if (msg.name !== "choose camp") {
    // Check if it's not "choose camp"
    wizardName.classList.add("inline");
    wizardName.textContent = msg.name; // Only update the wizard name if it's not "choose camp"
  }

  removeElement("checkFocus");
  const modalTitleElement = document.getElementById("wizardModalTitle");
  modalTitleElement.textContent = msg.name;

  // Remove existing close button if any
  removeElement("closeButton");

  removeElement("msg-img");
  displayHeaderModal(
    msg.type === "message" || msg.type === "camp" || msg.type === "camera",
    msg.name
  );

  if (!modalTitleElement.textContent.toLowerCase().includes("wizard")) {
    createCloseButton();
  }

  // Switch case to configure the modal based on message type
  switch (msg.type) {
    case "boolean":
      configureModalForInput("checkbox", msg.value);
      break;
    case "integer":
    case "floating":
      configureModalForInput("number", msg.value);
      break;
    case "str":
      configureModalForInput("text", msg.value);
      break;
    case "message":
      configureModalForMessage(msg.value);
      break;
    case "choice_integer":
    case "choice_floating":
    case "choice_str":
      configureModalForChoices("radio", msg.value, msg.choices);
      break;
    case "select_integer":
    case "select_floating":
    case "select_str":
      configureModalForChoices("select", msg.value, msg.choices);
      break;
    case "camp":
      configureModalForCamp(msg.value);
      break;
    case "camera":
      configureModalForCamera();
      break;
  }

  // Show the modal
  const wizardModal = document.getElementById("wizardModal");
  wizardModal.classList.remove("hidden");
  wizardModal.style.display = "flex";
}

function createCloseButton() {
  const closeButton = document.createElement("button"); // Set button text and attributes
  closeButton.innerHTML = "&times;"; // Close icon
  setAttributes(closeButton, {
    class: "absolute top-3 right-3 text-grey-color text-3xl leading-none hover:text-gray-400 focus:outline-none",
    'aria-label': "Close",
    id: 'closeButton',
    type: "button"
  });

  closeButton.addEventListener("click", () => {
    hideModal("wizardModal");
  });

  const modalBody = document.getElementById("wizardModalContent");
  modalBody.appendChild(closeButton);
  // Make sure the button is positioned absolutely in modalBody
  modalBody.classList.add("relative"); // Add relative positioning to modalBody
}

// Event listener for sending the wizard's input
document.getElementById("btnSendWizard").addEventListener("click", function () {
  const wizardNameText = document
    .getElementById("wizardName")
    .textContent.toLowerCase();
  let submittedValue = getSubmittedValue(wizardNameText); // Get the submitted value based on wizard type

  message.value = submittedValue; // Set the value to the message
  socket.emit("wizard", message); // Send the message through the socket

  hideModal("wizardModal"); // Hide the modal
});

// Function to get the submitted value based on the wizard type
function getSubmittedValue(wizardNameText) {
  if (wizardNameText.includes("camp")) {
    return document.getElementsByClassName("active")[0].getAttribute("value");
  }
  if (wizardNameText.includes("choose")) {
    return document.querySelector("input[name=choice]:checked").value;
  }
  if (wizardNameText.includes("select")) {
    return Array.from(
      document.querySelectorAll("input[name=choice]:checked")
    ).map((el) => el.value);
  }
  const wizardInput = document.getElementById("wizardInput");
  return wizardInput.getAttribute("type") === "checkbox"
    ? wizardInput.checked
    : wizardInput.value;
}

// Function to configure the modal for basic inputs (checkbox, text, number)
function configureModalForInput(typeInput, value) {
  textButtonWizard();
  formatWizardInput(true, typeInput, value);
}

// Function to configure the modal for choice-based inputs (radio or select)
function configureModalForChoices(typeInput, value, choices) {
  textButtonWizard();
  formatWizardInput(true, typeInput, value, choices);
}

// Function to configure the modal for displaying a message
function configureModalForMessage(value) {
  const wizardName = document.getElementById("wizardName");
  wizardName.textContent = value;

  const img = document.createElement("img"); // Create an image for the message
  setAttributes(img, {
    src: "static/img/message.svg",
    class: "inline",
    id: "msg-img",
  });

  const wizardModalTitle = document.getElementById("wizardModalTitle");
  wizardModalTitle.parentElement.insertBefore(img, wizardModalTitle); // Insert image before the title
  wizardModalTitle.classList.add("inline");

  textButtonWizard("Ok");
  formatWizardInput(false); // No input needed for messages
}

// Function to configure the modal for camp selection
function configureModalForCamp(value) {
  textButtonWizard();
  formatWizardInput(true, "camp", value);
}

// Function to configure the modal for camera streaming
function configureModalForCamera() {
  const streaming = document.createElement("img");
  setAttributes(streaming, {
    style: "width: 100%",
    src: `http://${window.location.hostname}:8081/`, // Load camera stream
  });

  const checkFocus = document.createElement("div");
  setAttributes(checkFocus, { id: "checkFocus" });
  checkFocus.appendChild(streaming);

  document.getElementById("modalBody").appendChild(checkFocus); // Add the streaming to the modal body

  textButtonWizard("Ok");
  formatWizardInput(false); // No input needed for camera
}

// Function to remove an element by ID
function removeElement(elementId) {
  const element = document.getElementById(elementId);
  if (element) element.parentNode.removeChild(element);
}

// Function to set attributes to an element
function setAttributes(element, attributes) {
  Object.keys(attributes).forEach((key) =>
    element.setAttribute(key, attributes[key])
  );
}

// Function to hide the modal
function hideModal(modalId) {
  const modal = document.getElementById(modalId);
  modal.classList.add("hidden");
  modal.style.display = "none";
}

// Function to display the modal header based on conditions
function displayHeaderModal(show = false, headerText = "") {
  const modalHeader = document.getElementById("modalHeader");
  modalHeader.style.display = show ? "block" : "none"; // Show or hide header

  if (show) {
    document.getElementById("wizardModalTitle").textContent =
      capitalizeFirstLetter(headerText);
  }
}

// Function to set the wizard button text
function textButtonWizard(text = "Send") {
  document.getElementById("btnSendWizard").textContent = text;
}

// Function to capitalize the first letter of a string
function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

// Function to format and configure the wizard input field
function formatWizardInput(showInput, typeInput, value, choices) {
  removeElement("newZone"); // Remove any previous input zones

  const wizardInput = document.getElementById("wizardInput");
  wizardInput.style.display = "none"; // Hide input by default
  wizardInput.value = "";
  wizardInput.removeAttribute("type"); // Clear previous input type

  if (showInput) {
    // Configure different types of inputs
    if (typeInput === "checkbox") {
      configureCheckboxInput(wizardInput, value);
    } else if (typeInput === "radio" || typeInput === "select") {
      configureChoiceInput(typeInput, value, choices);
    } else if (typeInput === "camp") {
      configureCampInput(value);
    } else {
      configureTextInput(wizardInput, value);
    }
  } else {
    wizardInput.style.display = "none"; // Hide input if not needed
  }
}

// Function to configure checkbox input
function configureCheckboxInput(wizardInput, value) {
  wizardInput.setAttribute(
    "class",
    "checked:accent-red-cogip checked:border-red-cogip"
  );
  wizardInput.checked = value;
}

// Function to configure choice-based inputs (radio or checkbox)
function configureChoiceInput(typeInput, value, choices) {
  const choiceZone = document.createElement("div");
  setAttributes(choiceZone, { id: "newZone", class: "max-h-[70vh] overflow-y-auto text-left" });

  const inputType = typeInput === "radio" ? "radio" : "checkbox";

  choices.forEach((choice, index) => {
     const button = createChoiceButton(inputType, choice, value, index); // Create a button for each choice
    const label = createChoiceLabel(choice, index); // Create a label for each choice

    // Add a margin to each choice (e.g., 8px space between each)
    const choiceWrapper = document.createElement("div");
    setAttributes(choiceWrapper, { class: "flex items-center mb-2" }); // mb-2 adds 8px margin at the bottom
    choiceWrapper.appendChild(button);
    choiceWrapper.appendChild(label);

   choiceZone.appendChild(choiceWrapper); // Append the choice with extra margin
  });

  document.getElementById("modalBody").appendChild(choiceZone); // Add choice input to modal body
}

// Helper function to create choice buttons (radio or checkbox)
function createChoiceButton(inputType, choice, value, index) {
  const isChecked =
    inputType === "radio" ? value == choice : value.indexOf(choice) >= 0;
  const button = document.createElement("input");
  setAttributes(button, {
    type: inputType,
    name: "choice",
    id: `choice-${index}`, // Unique ID for each input
    class:
      "w-[15px] h-[15px] me-2 rounded-md inline-block bg-white checked:accent-red-cogip",
    value: choice,
    checked: isChecked,
  });
  return button;
}
// Helper function to create labels for choice inputs
function createChoiceLabel(choice, index) {
  const label = document.createElement("label");
  setAttributes(label, {
    class: "text-grey-color",
    for: `choice-${index}`, // Link label to the input with the same ID
  });
  label.textContent = choice;
  return label;
}

// Function to configure camp-based input buttons
function configureCampInput(value) {
  const campZone = document.createElement("div");
  setAttributes(campZone, { id: "newZone" });

  const listCamp = ["blue", "yellow"];
  listCamp.forEach((camp) => {
    const isActive =
      camp === value ? "active shadow-lg shadow-black outline-none" : "";
    const button = createCampButton(camp, isActive); // Create camp buttons
    campZone.appendChild(button);
  });

  document.getElementById("modalBody").appendChild(campZone); // Add camp buttons to modal body
}

// Helper function to create camp buttons
function createCampButton(camp, isActive) {
  const cssColor = "camp-" + (camp === "blue" ? "1" : "2");
  const button = document.createElement("button");

  // Active state with scale, shadow, and translation for pressed effect
  setAttributes(button, {
    type: "button",
    class: `camp-button h-[30px] w-[100px] mr-[15px] bg-${cssColor} border-2 border-${cssColor} rounded-md 
            ${isActive} transition-all duration-200 transform 
            active:scale-95 active:translate-y-1 active:shadow-inner active:shadow-black/50`,
    value: camp,
  });

  // Event listener to activate and deactivate buttons
  button.addEventListener("click", function () {
    deactivateSiblings(this); // Deactivate sibling buttons
    this.classList.add("active", "shadow-lg", "shadow-black", "outline-none");
  });

  return button;
}

// Function to deactivate sibling elements (for camp buttons)
function deactivateSiblings(button) {
  Array.from(button.parentElement.children).forEach((sib) =>
    sib.classList.remove("active", "shadow-lg", "shadow-black", "outline-none")
  );
}

// Function to configure text-based inputs
function configureTextInput(wizardInput, value) {
  wizardInput.setAttribute(
    "class",
    "text-grey-color bg-black rounded-md border border-slate-950 use-keyboard-input focus:outline-none focus:caret-red-cogip focus:ring-2 focus:ring-red-cogip"
  );
  wizardInput.value = value; // Set input value
  wizardInput.style.display = "inline"; // Display the input
}
