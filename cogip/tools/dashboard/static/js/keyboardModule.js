export const virtualKeyboard = {
  elements: {
    mainNumpad: null,
    keysContainerNumpad: null,
    keysNumpad: null,
    mainFullKeyboard: null,
    keysContainerFullKeyboard: null,
    keysFullKeyBoard: null,
  },

  eventHandlers: {
    oninput: null,
    onclose: null,
  },

  properties: {
    value: "",
    capsLock: false,
  },

  init() {
    // Create parent container
    const parent = document.createElement("div");
    parent.classList.add("flex", "justify-center");

    const keyboards = [
      {
        type: "mainNumpad",
        container: "keysContainerNumpad",
        keys: "keysNumpad",
        layout: "number",
      },
      {
        type: "mainFullKeyboard",
        container: "keysContainerFullKeyboard",
        keys: "keysFullKeyBoard",
        layout: "text",
      },
    ];

    keyboards.forEach(({ type, container, keys, layout }) => {
      this.elements[type] = this._createElement("div", [
        "z-100",
        "fixed",
        "bottom-0",
        "hidden",
        "ml-auto",
        "mr-auto",
        "select-none",
        "transition-bottom",
        "bg-black",
        "rounded-lg"
      ]);


      if (layout === "text") {
        this.elements[type].classList.add("w-full");
      } else {
        this.elements[type].classList.add("w-[300px]"); // Height adapted to Numpad
      }


      this.elements[container] = this._createElement("div", ["text-center"]);
      this.elements[container].appendChild(this._createKeys(layout));

      this.elements[keys] =
        this.elements[container].querySelectorAll(".bg-custom-button");

      // Add elements to DOM
      this.elements[type].appendChild(this.elements[container]);
      parent.append(this.elements[type]);
      document.body.appendChild(parent);
    });
  },

  _createElement(tag, classes) {
    const el = document.createElement(tag);
    el.classList.add(...classes);
    return el;
  },

  _createKeys(layoutType) {
    const fragment = document.createDocumentFragment();
    let keyLayout =
      layoutType === "text"
        ? [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
            "backspace",
            "a",
            "z",
            "e",
            "r",
            "t",
            "y",
            "u",
            "i",
            "o",
            "p",
            "caps",
            "q",
            "s",
            "d",
            "f",
            "g",
            "h",
            "j",
            "k",
            "l",
            "m",
            "w",
            "x",
            "c",
            "v",
            "b",
            "n",
            ",",
            ".",
            "space",
          ]
        : ["9", "8", "7", "6", "5", "4", "3", "2", "1", "0", ".", "backspace"];

    const lineBreaks =
      layoutType === "text" ? ["backspace", "p", "m", "."] : ["7", "4", "1"];

    keyLayout.forEach((key) => {
      const keyElement = this._createElement("button", [
        "inline-flex",
        "h-[45px]",
        "max-w-[85px]",
        "w-[30%]",
        "m-1",
        "items-center",
        "justify-center",
        "align-middle",
        "bg-custom-button",
        "rounded-md",
        "border-none",
        "outline-none",
        "text-red-cogip",
        "cursor-pointer",
      ]);
      this._setupKey(key, keyElement);

      fragment.appendChild(keyElement);
      if (lineBreaks.includes(key))
        fragment.appendChild(document.createElement("br"));
    });

    return fragment;
  },

  _setupKey(key, keyElement) {
    switch (key) {
      case "backspace":
        keyElement.innerHTML = "<img src='static/img/backspace.svg'></img>";
        keyElement.addEventListener("click", () => this._handleBackspace());
        break;

      case "caps":
        keyElement.innerHTML = "<img src='static/img/caps_lock.svg'></img>";
        keyElement.addEventListener("click", () => this._toggleCapsLock());
        break;

      case "space":
        keyElement.innerHTML = "<img src='static/img/space_bar.svg'></img>";
        keyElement.classList.replace("max-w-[85px]", "w-[36%]");
        keyElement.addEventListener("click", () => this._handleSpace());
        break;

      default:
        keyElement.textContent = key.toLowerCase();
        keyElement.addEventListener("click", () => this._handleKeyPress(key));
    }
  },

  _handleBackspace() {
    this.properties.value = this.properties.value.slice(0, -1);
    this._triggerEvent("oninput");
  },

  _handleSpace() {
    this.properties.value += " ";
    this._triggerEvent("oninput");
  },

  _handleKeyPress(key) {
    this.properties.value += this.properties.capsLock
      ? key.toUpperCase()
      : key.toLowerCase();
    this._triggerEvent("oninput");
  },

  _triggerEvent(handlerName) {
    if (typeof this.eventHandlers[handlerName] === "function") {
      this.eventHandlers[handlerName](this.properties.value);
    }
  },

  _toggleCapsLock() {
    this.properties.capsLock = !this.properties.capsLock;
    this.elements.keysFullKeyBoard.forEach((key) => {
      if (key.childElementCount === 0) {
        key.textContent = this.properties.capsLock
          ? key.textContent.toUpperCase()
          : key.textContent.toLowerCase();
      }
    });
  },

  open(type, initialValue, oninput, onclose) {
    this.properties.value = initialValue || "";
    this.eventHandlers.oninput = oninput;
    this.eventHandlers.onclose = onclose;
    this.elements[
      type === "text" ? "mainFullKeyboard" : "mainNumpad"
    ].classList.remove("hidden");
  },

  close() {
    this.properties.value = "";
    this.eventHandlers.oninput = null;
    this.eventHandlers.onclose = null;
    this.elements.mainNumpad.classList.add("hidden");
    this.elements.mainFullKeyboard.classList.add("hidden");
  },

  _actualize() {
    document.querySelectorAll(".use-keyboard-input").forEach((element) => {
      element.addEventListener("click", () => {
        virtualKeyboard.open(
          element.type,
          element.value,
          (value) => (element.value = value)
        );
      });
    });

    document.addEventListener("click", (event) => {
      if (
        !event.target.closest(".use-keyboard-input") &&
        !event.target.closest(".bg-custom-button") &&
        !event.target.closest(".text-center")
      ) {
        this.close();
      }
    });
  },
};
