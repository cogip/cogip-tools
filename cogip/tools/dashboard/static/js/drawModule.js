let pose_current = {}, pose_order = {}, path = {}, obstacles = {};
const robotImages = {}, orderImages = {}, cachedElements = {};
const robotColors = {
  1: "#F0A30A",
  2: "#3A5431",
  3: "#432D57",
  4: "#001DBC",
};

let ratioX = null, ratioY = null,  coordX = 0, coordY = 0;

// Preload robot and order images
(function loadImages() {
  for (let i = 1; i <= 4; i++) {
    robotImages[i] = new Image();
    orderImages[i] = new Image();
    robotImages[i].src = `static/img/robot${i}.png`;
    orderImages[i].src = `static/img/robot${i}.png`;
  }
})();

// Element caching for performance
const cacheElement = (selector) => {
  if (!cachedElements[selector]) {
    cachedElements[selector] = document.querySelector(selector);
  }
  return cachedElements[selector];
};

// Pose updates
export const updatePoseCurrent = (robot_id, new_pose) => (pose_current[robot_id] = new_pose);
export const updatePoseOrder = (robot_id, new_pose) => (pose_order[robot_id] = new_pose);
export const recordPath = (robot_id, msg) => (path[robot_id] = msg);
export const updateObstacles = (robot_id, new_obstacles) => (obstacles[robot_id] = new_obstacles);

// Retrieve image
const getImage = (robot_id, type) => (type === "robot" ? robotImages : orderImages)[robot_id] || new Image();

// Element height computation
const getFullHeight = (className, includeMargin = true) => {
  const element = cacheElement(`.${className}`);
  if (!element) return 0;
  const styles = window.getComputedStyle(element);
  const margin = includeMargin ? parseFloat(styles.marginTop) + parseFloat(styles.marginBottom) : 0;
  return element.offsetHeight + margin;
};

export function resizeCanvas() {
  const footerHeight = getFullHeight("footer", false);
  const navHeight = getFullHeight("flex-wrap", true);
  const menuWidth = cacheElement("#menu").offsetWidth;
  const canvas = cacheElement("#board");
  const menuHeight = cacheElement("#menu").offsetHeight;

  canvas.height = Math.min(
    window.innerHeight - (footerHeight + navHeight),
    menuHeight
  );
  canvas.width = window.innerWidth - menuWidth - 10;

  const imgRatio = 2/3;
  const adjustedHeight = Math.min(canvas.height, canvas.width * imgRatio);
  const adjustedWidth = adjustedHeight * (3 / 2);

  const context = canvas.getContext("2d");
  context.canvas.width = adjustedWidth;
  context.canvas.height = adjustedHeight;

  coordX = 0;
  coordY = canvas.height / 2;
  context.translate(coordX, coordY);

  ratioX = adjustedWidth / 3000;
  ratioY = -adjustedHeight / 2000;
  setButtonPosition(canvas);
}

function setButtonPosition(canvas) {
  const menuWidth = cacheElement("#menu").offsetWidth;
  const rightPx = Math.max(window.innerWidth - menuWidth - canvas.width, 0);
  const buttonRefresh = cacheElement("#buttonRefresh");
  buttonRefresh.style.right = `${rightPx}px`;

  const buttonCameraModal = cacheElement("#buttonCameraModal");
  if (buttonCameraModal) {
    buttonCameraModal.style.top = `${canvas.height - 44}px`; // 44 is the height of the camera image
    buttonCameraModal.style.right = `${rightPx - 59}px`; // 59 is the width of the refresh image
  }
}

export function displayMsg(robot_id, msg) {
  const stateHTML = cacheElement(`#state_robot_${robot_id}`);
  const pose = pose_current[robot_id];

  if (pose && !isNaN(pose.x) && !isNaN(pose.y)) {
    stateHTML.textContent = `R.${robot_id} Cy.:${
      msg.cycle
    } / X:${pose.x.toFixed(2)} / Y:${pose.y.toFixed(2)} / Ang:${pose.O.toFixed(
      2
    )}`;
  }
}

// Main function
(function drawFrame() {
  const canvas = cacheElement("#board");
  const context = canvas.getContext("2d");

  // Clear canvas
  context.clearRect(coordX, -coordY, canvas.width, canvas.height);

  Object.entries(pose_current).forEach(([robot_id, pose]) => {
    // Check if current position is valid
    if (pose && !isNaN(pose.x) && !isNaN(pose.y)) {
      drawRobot(getImage(robot_id, "robot"), pose.x, pose.y, pose.O, context);
    }

    // Draw orderPose
    const orderPose = pose_order[robot_id];
    if (orderPose) {
      const previousFilter = context.filter;
      context.filter = "opacity(60%)";
      drawRobot(
        getImage(robot_id, "order"),
        orderPose.x,
        orderPose.y,
        orderPose.O,
        context
      );
      context.filter = previousFilter;
    }

    drawPathsAndObstacles(robotColors[robot_id] || "red", robot_id, context);
  });

  // Refresh canvas continuously.
  requestAnimationFrame(drawFrame);
})();

function drawPathsAndObstacles(color, robot_id, context) {
  const pathRobot = path[robot_id] || [];
  const pose = pose_current[robot_id];

  // Draw the path
  if (pose && pathRobot.length > 1) {
    pathRobot.reduce((prev, curr) => {
      drawPath(color, prev, curr, context);
      return curr;
    });
  }

  // Draw obstacles
  const obstaclesRobot = obstacles[robot_id] || [];
  obstaclesRobot.forEach((obstacle) => {
    drawObstacles(color, obstacle, context);
  });
}

const adaptCoords = (x, y, angle) => ({
  x: 1500 - y,
  y: x,
  angle: -angle - 90,
});

function drawRobot(robot, x, y, angle, context) {
  const { x: newX, y: newY, angle: newAngle } = adaptCoords(x, y, angle);
  const robotWidth = robot.width * ratioX;
  const robotHeight = robot.height * ratioY;

  context.translate(newX * ratioX, newY * ratioY);
  context.rotate((newAngle * Math.PI) / 180);
  context.drawImage(
    robot,
    -robotWidth / 2,
    -robotHeight / 2,
    robotWidth,
    robotHeight
  );

  context.rotate(-(newAngle * Math.PI) / 180);
  context.translate(-newX * ratioX, -newY * ratioY);
}

function drawPath(color, start, end, context) {
  const startCoords = adaptCoords(start.x, start.y, 0);
  const endCoords = adaptCoords(end.x, end.y, 0);
  const previousStrokeStyle = context.strokeStyle;
  const previousLineWidth = context.lineWidth;

  context.strokeStyle = color;
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(startCoords.x * ratioX, startCoords.y * ratioY);
  context.lineTo(endCoords.x * ratioX, endCoords.y * ratioY);
  context.stroke();

  context.strokeStyle = previousStrokeStyle;
  context.lineWidth = previousLineWidth;
}

function drawObstacles(color, obstacle, context) {
  const { x, y, angle } = adaptCoords(obstacle.x, obstacle.y, 0);
  const obstacleX = x * ratioX;
  const obstacleY = y * ratioY;

  const previousFilter = context.filter;
  context.fillStyle = obstacle.id ? "purple" : color;
  context.filter = "opacity(40%)";

  if (obstacle.radius) {
    const radius = obstacle.radius * ratioX; // Precalculate radius
    context.beginPath();
    context.arc(obstacleX, obstacleY, radius, 0, 2 * Math.PI);
    context.fill();
  } else {
    const lengthX = obstacle.length_x * ratioX;
    const lengthY = obstacle.length_y * ratioY;

    context.translate(obstacleX, obstacleY);
    context.rotate((angle * Math.PI) / 180);
    context.fillRect(
      -lengthX / 2,
      -lengthY / 2,
      lengthX, lengthY
    );
    context.rotate(-(angle * Math.PI) / 180);
    context.translate(-obstacleX, -obstacleY);
  }

  context.filter = previousFilter;
}

export function addNewTab(robot_id) {
  //Check if nav-tab already exists and remove it
  const existingNavTab = cacheElement(`#robot${robot_id}-tab`);
  if (existingNavTab) {
    existingNavTab.parentElement.remove();
    const parent = existingNavTab.parentElement;
    parent.replaceWith(parent.cloneNode(true));
  }

  //Check if tab-tab already exists and remove it
  const existingTabPane = cacheElement(`#robot${robot_id}`);
  if (existingTabPane) {
    existingTabPane.remove();
  }

  // Create new nav-tab element
  var newNavTab = document.createElement("li");
  newNavTab.className = "mr-2";
  newNavTab.innerHTML = `
  <button
    class="inline-block px-4 py-2 text-gray-600 hover:text-red-cogip border-b-2 border-transparent hover:border-red-cogip focus:outline-none"
    id="robot${robot_id}-tab"
    data-target="#robot${robot_id}"
    type="button"
    role="tab"
    aria-controls="robot${robot_id}"
    aria-selected="false">
    Robot ${robot_id}
  </button>`;

  // Create new tab-pane element
  var newTabPane = document.createElement("div");
  newTabPane.className = "hidden";
  newTabPane.id = `robot${robot_id}`;
  newTabPane.setAttribute("role", "tabpanel");

  var navTabHeight = getFullHeight("flex-wrap", true);
  newTabPane.innerHTML = `
  <iframe
    id="robot${robot_id}-iframe"
    style="position: absolute; top: ${navTabHeight}px; bottom: 0; left: 0; right: 0; width: 100%; height: ${
    window.innerHeight - navTabHeight
  }px;"
    class="w-full h-full"
    frameborder="0">
  </iframe>`;

  // Append new nav-tab to the flex-wrap container
  const navTabsContainer = cacheElement(".flex-wrap");
  navTabsContainer.appendChild(newNavTab);

  // Append new tab-pane to the tab-content container
  const tabContentContainer = cacheElement(".tab-content");
  tabContentContainer.appendChild(newTabPane);
}

export function deleteTab(robot_id) {
  // Select the nav-tab and tab-pane elements
  const navButton = cacheElement(`#robot${robot_id}-tab`);
  const navTab = navButton?.parentElement;
  const tabPane = cacheElement(`#robot${robot_id}`);

  // Check if elements exist before attempting removal
  if (navTab && tabPane) {
    const navTabsContainer = cacheElement(".flex-wrap");
    navTabsContainer?.removeChild(navTab);

    const tabContentContainer = cacheElement(".tab-content");
    tabContentContainer?.removeChild(tabPane);

    // Activate beacon tab if the deleted tab was active
    if (navButton?.classList.contains("active")) {
      const beaconButton = cacheElement("#beacon-tab");
      beaconButton?.classList.add("active");
      const beaconPane = cacheElement("#beacon");
      beaconPane?.classList.add("active", "show");
    }
  }
}

export function deleteTabs() {
  document.querySelectorAll('[id^="robot"][id$="-tab"]').forEach((x) => {
    const match = x.id.match(/robot(\d+)-tab/);
    if (match) {
      deleteTab(parseInt(match[1], 10));
    }
  });
}
