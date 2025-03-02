window.openChartModal = function () {
  const chartModal = document.getElementById("chartModal");
  chartModal.classList.remove("hidden");
  chartModal.classList.add("flex");
};

const ctxDistance = document.getElementById("distanceChart").getContext("2d");
const ctxAngle = document.getElementById("angleChart").getContext("2d");
let distanceChart = null;
let angleChart = null;

// draw empty Charts
export function drawCharts() {
  distanceChart = new Chart(ctxDistance, {
    type: "line",
    data: {
      labels: [], // WIll contains cycle
      datasets: [
        {
          label: "Speed Current Distance",
          data: [], // Dynamics Data
          borderColor: "blue",
          fill: false,
        },
        {
          label: "Speed Order Distance",
          data: [], // Dynamics Data
          borderColor: "green",
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: "Cycle",
          },
        },
        y: {
          title: {
            display: true,
            text: "Distance",
          },
        },
      },
    },
  });

  angleChart = new Chart(ctxAngle, {
    type: "line",
    data: {
      labels: [], // Will contains cycle
      datasets: [
        {
          label: "Speed Current Angle",
          data: [], // Dynamics Data
          borderColor: "red",
          fill: false,
        },
        {
          label: "Speed Order Angle",
          data: [], // Dynamics Data
          borderColor: "orange",
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: "Cycle",
          },
        },
        y: {
          title: {
            display: true,
            text: "Angle",
          },
        },
      },
    },
  });
}

// Update charts
export function updateCharts(msg) {
  const cycle = msg.cycle;
  const currentDistance = msg.speed_current?.distance ?? null;
  const orderDistance = msg.speed_order?.distance ?? null;
  const currentAngle = msg.speed_current?.angle ?? null;
  const orderAngle = msg.speed_order?.angle ?? null;

  if (distanceChart.data.labels.length > 50) {
    // Limit at 50 cycles to avoid overflow
    distanceChart.data.labels.shift();
    distanceChart.data.datasets[0].data.shift();
    distanceChart.data.datasets[1].data.shift();
  }
  distanceChart.data.labels.push(cycle);
  distanceChart.data.datasets[0].data.push(currentDistance);
  distanceChart.data.datasets[1].data.push(orderDistance);
  distanceChart.update();

  // Update angle chart
  if (angleChart.data.labels.length > 50) {
    // Limit at 50 cycles to avoid overflow
    angleChart.data.labels.shift();
    angleChart.data.datasets[0].data.shift();
    angleChart.data.datasets[1].data.shift();
  }
  angleChart.data.labels.push(cycle);
  angleChart.data.datasets[0].data.push(currentAngle);
  angleChart.data.datasets[1].data.push(orderAngle);
  angleChart.update();
}
