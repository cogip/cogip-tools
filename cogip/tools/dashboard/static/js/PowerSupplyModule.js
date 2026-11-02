const unknown = "—";
const stateClasses = ["good", "bad", "muted"];

const rails = ["p3V3", "p5V0", "p7V5", "pxVx", "p12V0"];
const pgoodRails = ["p3V3", "p5V0", "p7V5", "pxVx"];

// Display a state as an icon and text.
// If the state is unknown, display "—".
function setState(id, ok, text) {
  const element = document.getElementById(id);
  if (!element) return;

  // Skip unchanged states: periodic messages would otherwise recreate the icon and make it blink.
  const state = ok === null || ok === undefined ? "unknown" : `${ok}:${text}`;
  if (element.dataset.state === state) return;
  element.dataset.state = state;

  if (ok === null || ok === undefined) {
    element.textContent = unknown;
    element.classList.remove(...stateClasses);
    element.classList.add("muted");
    return;
  }

  const img = document.createElement("img");
  img.src = `/static/img/${
    ok ? "check_green_circle" : "cross_red_circle"
  }.svg`;
  img.alt = ok ? "OK" : "Fault";
  img.width = 20;
  img.height = 20;
  img.style.display = "inline"; // Tailwind preflight makes images block-level
  img.style.verticalAlign = "middle";
  img.style.marginRight = "8px";

  element.replaceChildren(img, document.createTextNode(text));
  element.classList.remove(...stateClasses);
  element.classList.add(ok ? "good" : "bad");
}

function setText(id, text) {
  const element = document.getElementById(id);
  if (element) element.textContent = text;
}

export function updateEmergencyStop(status) {
  const engaged = status?.emergency_stop_engaged;
  const released = typeof engaged === "boolean" ? !engaged : null;

  setState(
    "powerEmergencyStop",
    released,
    released ? "Released" : "Engaged"
  );
}

export function updatePowerSource(status) {
  const battery = status ? status.battery_valid : null;
  const dcSupply = status ? status.dc_supply_valid : null;

  setState(
    "powerBattery",
    battery,
    battery ? "Connected" : "Disconnected"
  );

  setState(
    "powerDcSupply",
    dcSupply,
    dcSupply ? "Connected" : "Disconnected"
  );
}

export function updatePowerRailsStatus(status) {
  pgoodRails.forEach((rail) => {
    const pgood = status
      ? status[`${rail}_pgood`]
      : null;

    setState(
      `rail_${rail}_pgood`,
      pgood,
      pgood ? "OK" : "Fault"
    );
  });
}

export function updatePowerRailsMeasures(measures) {
  rails.forEach((rail) => {
    const measure = measures ? measures[rail] : null;

    if (!measure) {
      setText(`rail_${rail}_voltage`, unknown);
      setText(`rail_${rail}_current`, unknown);
      setText(`rail_${rail}_power`, unknown);
      return;
    }

    // Number(null) and Number("") return 0: only accept actual numbers.
    const voltage = typeof measure.voltage_mv === "number" ? measure.voltage_mv : NaN;
    const current = typeof measure.current_ma === "number" ? measure.current_ma : NaN;

    setText(
      `rail_${rail}_voltage`,
      Number.isFinite(voltage) ? (voltage / 1000).toFixed(2) : unknown
    );

    setText(
      `rail_${rail}_current`,
      Number.isFinite(current) ? current.toFixed(0) : unknown
    );

    setText(
      `rail_${rail}_power`,
      Number.isFinite(voltage) && Number.isFinite(current)
        ? ((voltage * current) / 1e6).toFixed(2)
        : unknown
    );
  });
}

// Reset displayed values when the server connection is lost.
export function reset() {
  updateEmergencyStop(null);
  updatePowerSource(null);
  updatePowerRailsStatus(null);
  updatePowerRailsMeasures(null);
}
