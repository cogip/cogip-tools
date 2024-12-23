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
    // Create main elements
    const parent = document.createElement("div");
    parent.classList.add("row");

    const listKeyboard = [
      {
        type: "mainNumpad",
        keysContainer: "keysContainerNumpad",
        keys: "keysNumpad",
        neededKeys: "number",
      },
      {
        type: "mainFullKeyboard",
        keysContainerkeys: "keysContainerFullKeyboard",
        keys: "keysFullKeyBoard",
        neededKeys: "text",
      },
    ];

    listKeyboard.forEach((obj) => {
      let type = obj.type;
      let keysContainer = obj.keysContainer;
      let keys = obj.keys;

      this.elements[type] = document.createElement("div");
      this.elements[keysContainer] = document.createElement("div");

      // Setup main elements for numpad
      this.elements[type].classList.add("keyboard", "keyboard--hidden");

      if (obj.neededKeys !== "text") {
        this.elements[type].classList.add("w-25", "offset-md-5");
      }
      this.elements[keysContainer].classList.add("keyboard__keys");
      this.elements[keysContainer].appendChild(
        this._createKeys(obj.neededKeys)
      );

      this.elements[keys] =
        this.elements[keysContainer].querySelectorAll(".keyboard__key");

      // Add to DOM
      this.elements[type].appendChild(this.elements[keysContainer]);
      parent.append(this.elements[type]);
      document.body.appendChild(parent);
    });
  },

  _createKeys(type) {
    const fragment = document.createDocumentFragment();
    let keyLayout = [
      "9",
      "8",
      "7",
      "6",
      "5",
      "4",
      "3",
      "2",
      "1",
      "0",
      ".",
      "backspace",
    ];

    let lineBreak = ["7", "4", "1"];

    if (type === "text") {
      keyLayout = [
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
      ];

      lineBreak = ["backspace", "p", "m", "."];
    }

    keyLayout.forEach((key) => {
      const keyElement = document.createElement("button");
      const insertLineBreak = lineBreak.indexOf(key) !== -1;

      // Add attributes/classes
      keyElement.setAttribute("type", "button");
      keyElement.classList.add("keyboard__key");

      switch (key) {
        case "backspace":
          keyElement.innerHTML = '<img src="static/img/backspace.svg"></img>';

          keyElement.addEventListener("click", () => {
            this.properties.value = this.properties.value.substring(
              0,
              this.properties.value.length - 1
            );
            this._triggerEvent("oninput");
          });
          break;

        case "caps":
          keyElement.innerHTML = '<img src="static/img/caps_lock.svg"></img>';
          keyElement.classList.add(
            "keyboard__key--wide",
            "keyboard__key--activate"
          );

          keyElement.addEventListener("click", () => {
            this._toggleCapsLock();
            keyElement.classList.toggle(
              "keyboard__key--active",
              this.properties.capsLock
            );
          });

          break;

        case "space":
          keyElement.innerHTML = '<img src="static/img/space_bar.svg"></img>';
          keyElement.classList.add("keyboard__key--extra-wide");

          keyElement.addEventListener("click", () => {
            this.properties.value += " ";
            this._triggerEvent("oninput");
          });

          break;

        default:
          keyElement.textContent = key.toLowerCase();

          keyElement.addEventListener("focus", () => {
            this.properties.value += this.properties.capsLock
              ? key.toUpperCase()
              : key.toLowerCase();
            this._triggerEvent("oninput");
          });
      }

      fragment.appendChild(keyElement);

      if (insertLineBreak) {
        fragment.appendChild(document.createElement("br"));
      }
    });
    return fragment;
  },

  _triggerEvent(handlerName) {
    if (typeof this.eventHandlers[handlerName] == "function") {
      this.eventHandlers[handlerName](this.properties.value);
    }
  },

  _toggleCapsLock() {
    this.properties.capsLock = !this.properties.capsLock;

    for (const key of this.elements.keysFullKeyBoard) {
      if (key.childElementCount === 0) {
        key.textContent = this.properties.capsLock
          ? key.textContent.toUpperCase()
          : key.textContent.toLowerCase();
      }
    }
  },

  open(type, initialValue, oninput, onclose) {
    this.properties.value = initialValue || "";
    this.eventHandlers.oninput = oninput;
    this.eventHandlers.onclose = onclose;
    if (type === "text") {
      this.elements.mainFullKeyboard.classList.remove("keyboard--hidden");
    } else {
      this.elements.mainNumpad.classList.remove("keyboard--hidden");
    }
  },

  close() {
    this.properties.value = "";
    this.eventHandlers.oninput = oninput;
    this.eventHandlers.onclose = onclose;
    this.elements.mainNumpad.classList.add("keyboard--hidden");
    this.elements.mainFullKeyboard.classList.add("keyboard--hidden");
  },

  _actualize() {
    // Automatically use keyboard for elements with .use-keyboard-input
    document.querySelectorAll(".use-keyboard-input").forEach((element) => {
      element.addEventListener("click", () => {
        virtualKeyboard.open(element.type, element.value, (currentValue) => {
          element.value = currentValue;
        });
      });
    });

    let virtualKeyboard = this;
    document.addEventListener("click", function (event) {
      if (
        event.target.closest(".use-keyboard-input") === null &&
        event.target.closest(".keyboard__key") === null
      ) {
        virtualKeyboard.close();
      }
    });
  },
};
