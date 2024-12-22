export function openScoreModal(score) {
  const scoreDisplay = document.getElementById("displayScore");
  const scoreModal = document.getElementById("scoreModal");

  // Error handling for missing elements
  if (!scoreDisplay || !scoreModal) {
    console.error("Score display or modal element not found.");
    return;
  }

  // Set the score and show the modal
  scoreDisplay.textContent = score;
  scoreModal.classList.remove("hidden");
  scoreModal.classList.add("flex"); // Consider using class manipulation for consistency
}