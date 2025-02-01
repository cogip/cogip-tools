let socket = null;

export function openConfigModal(config, send_socket) {
  socket = send_socket;
  document.getElementById("configModalHeader").textContent = config.title;

  const form = document.createElement("div");
  form.classList.add("grid", "grid-cols-2", "gap-4", "items-center");

  Object.entries(config.properties).forEach(([key, property]) => {
    const label = document.createElement("label");
    label.textContent = property.title;
    label.classList.add("font-medium", "text-grey-color", "text-left");
    label.setAttribute("key", key);

    const fieldContainer = document.createElement("div");
    fieldContainer.classList.add("flex", "items-center", "gap-2");

    if (property.type === "boolean") {
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = property.value;
      checkbox.classList.add("form-checkbox", "h-5", "w-5", "checked:accent-red-cogip", "checked:border-red-cogip");
      checkbox.addEventListener("change", () => {
        sendSocketUpdate(
          config.sio_event,
          key,
          checkbox.checked,
          config.namespace
        );
      });
      fieldContainer.appendChild(checkbox);
    } else if (property.type === "integer" || property.type === "number") {
      const input = document.createElement("input");
      input.type = "number";
      input.value = property.value;
      input.min = property.minimum;
      input.max = property.maximum;
      input.classList.add("border", "p-2", "rounded", "w-full");

      const slider = document.createElement("input");
      slider.type = "range";
      slider.min = property.minimum;
      slider.max = property.maximum;
      slider.value = property.value;
      slider.step = property.multipleOf || 1;
      slider.classList.add(
        "w-full",
        "appearance-none",
        "h-2",
        "bg-gray-300",
        "rounded-full",
        "thumb-red-500"
      );

      input.addEventListener("input", () => {
        slider.value = input.value;
        sendSocketUpdate(config.sio_event, key, input.value, config.namespace);
      });
      slider.addEventListener("input", () => {
        input.value = slider.value;
        sendSocketUpdate(config.sio_event, key, slider.value, config.namespace);
      });
      fieldContainer.appendChild(input);
      fieldContainer.appendChild(slider);
    }

    form.appendChild(label);
    form.appendChild(fieldContainer);
  });

  document.getElementById("configModalBody").appendChild(form);

  // Show the modal
  const configModal = document.getElementById("configModal");
  configModal.classList.remove("hidden");
  configModal.style.display = "flex";
}

function sendSocketUpdate(event, name, value, namespace) {
  const socketUpdate = {
    name: name,
    namespace: namespace,
    sio_event: event,
    value: value,
  };
  socket.emit(event, socketUpdate);
}
