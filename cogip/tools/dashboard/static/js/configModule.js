let socket = null;

export function openConfigModal(config, send_socket) {
  socket = send_socket;
  document.getElementById("configModalTitle").textContent = config.title;

  document.getElementById("configModalBody").innerHTML = "";

  const form = document.createElement("div");
  form.classList.add("grid", "grid-cols-[30%_67%]", "gap-4", "items-center");

  Object.entries(config.properties).forEach(([key, property]) => {
    if (property.value === undefined) {
      // Value is not set for properties with excluded=True
      return;
    }

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
      input.style.width = '75px';
      input.disabled = true;
      input.classList.add(
        "text-grey-color",
        "p-2",
        "bg-black",
        "rounded-md",
        "border",
        "border-slate-950",
        "use-keyboard-input",
        "focus:outline-hidden",
        "focus:caret-red-cogip",
        "focus:ring-2",
        "focus:ring-red-cogip"
      );

      const slider = document.createElement("input");
      slider.type = "range";
      slider.min = property.minimum;
      slider.max = property.maximum;
      slider.value = property.value;
      slider.step = property.multipleOf || 1;
      slider.classList.add(
        "w-full",
        "appearance-none",
        "h-4",
        "bg-gray-300",
        "rounded-full",
        "thumb-red-cogip"
      );

      const decrementBtn = document.createElement("button");
      decrementBtn.textContent = "-";
      decrementBtn.classList.add(
        "px-4",
        "py-2",
        "text-2xl",
        "bg-zinc-800",
        "text-grey-color",
        "rounded-sm",
        "hover:bg-gray-600",
        "focus:outline-hidden"
      );
      decrementBtn.addEventListener("click", () => {
        let newValue = Math.max(
          parseFloat(input.value) - (property.multipleOf || 1),
          property.minimum
        );
        newValue = parseFloat(newValue.toFixed(3));
        input.value = slider.value = newValue;
        sendSocketUpdate(config.sio_event, key, newValue, config.namespace);
      });

      const incrementBtn = document.createElement("button");
      incrementBtn.textContent = "+";
      incrementBtn.classList.add("px-4", "py-2", "text-2xl", "bg-zinc-800", "text-grey-color", "rounded-sm",  "hover:bg-gray-600", "focus:outline-hidden");
      incrementBtn.addEventListener("click", () => {
        let newValue = Math.min(
          parseFloat(input.value) + (property.multipleOf || 1),
          property.maximum
        );
        newValue = parseFloat(newValue.toFixed(3));
        input.value = slider.value = newValue;
        sendSocketUpdate(config.sio_event, key, newValue, config.namespace);
      });

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
      fieldContainer.appendChild(decrementBtn);
      fieldContainer.appendChild(incrementBtn);
    }

    form.appendChild(label);
    form.appendChild(fieldContainer);
  });

  document.getElementById("configModalBody").appendChild(form);

  // Show the modal
  const configModal = document.getElementById("configModal");
  configModal.classList.remove("hidden");
  configModal.classList.add("flex");
}

function sendSocketUpdate(event, name, value, namespace) {
  const socketUpdate = {
    name: name,
    namespace: namespace,
    sio_event: event,
    value: +value,
  };
  socket.emit("config_updated", socketUpdate);
}
