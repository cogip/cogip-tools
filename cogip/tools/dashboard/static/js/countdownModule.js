export function openCountdownModal(countdown) {
  const countdownDisplay = document.getElementById("displayCountdown");
  const countdownModal = document.getElementById("countdownModal");

  // Error handling for missing elements
  if (!countdownDisplay || !countdownModal) {
    console.error("Countdown display or modal element not found.");
    return;
  }

  countdownModal.classList.remove("hidden");
  countdownModal.classList.add("flex");
  countdownDisplay.style.color = ""; // Reset to default

  // Clear any previous interval
  if (window._countdownInterval) {
    clearInterval(window._countdownInterval);
  }

  const startTime = Date.now();
  const endTime = startTime + countdown * 1000;
  const intervalMs = 200;

  function updateCountdown() {
    const now = Date.now();
    const remaining = (endTime - now) / 1000;
    countdownDisplay.textContent = remaining.toFixed(2);

    // Change color to red if less than or equal to 15 seconds
    if (remaining <= 15) {
      countdownDisplay.style.color = "red";
    }

    if (remaining <= 0) {
      clearInterval(window._countdownInterval);
      countdownModal.classList.add("hidden");
      countdownModal.classList.remove("flex");
    }
  }

  updateCountdown();
  window._countdownInterval = setInterval(updateCountdown, intervalMs);
}
