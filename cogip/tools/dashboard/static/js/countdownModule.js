window.modalCountdown = function () {
  const countdownModal = document.getElementById("countdownModal");
  if (countdownModal.classList.contains("hidden")) {
    countdownModal.classList.remove("hidden");
    countdownModal.classList.add("flex");
  }
}

export function openCountdownModal(robot_id, countdown, start, color) {
  const countdownDisplay = document.getElementById(
    `displayCountdown_${robot_id}`
  );
  const countdownModal = document.getElementById("countdownModal");
  // Error handling for missing elements
  if (!countdownDisplay || !countdownModal) {
    console.error("Countdown display or modal element not found.");
    return;
  }

  modalCountdown(); // Ensure the modal is open
  countdownDisplay.style.color = ""; // Reset to default

  // Clear any previous interval
  if (window._countdownInterval && window._countdownInterval[robot_id]) {
    clearInterval(window._countdownInterval[robot_id]);
  }

  const startTime = new Date(start).getTime();
  const endTime = startTime + countdown * 1000;
  const intervalMs = 200;

  function updateCountdown(robot_id, color) {
    const now = Date.now();
    const remaining = (endTime - now) / 1000;
    const display = document.getElementById(`displayCountdown_${robot_id}`);

    display.textContent = remaining.toFixed(2);

    // Change color to red if less than or equal to 15 seconds
    if (color) {
      display.style.color = color;

    }
  }

  updateCountdown(robot_id, color);
  if (!window._countdownInterval) {
    window._countdownInterval = {};
  }

  window._countdownInterval[robot_id] = setInterval(
    () => updateCountdown(robot_id, color),
    intervalMs
  );
}
