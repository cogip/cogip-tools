let pose_current = {};
let pose_order = {};
let path = {};
let obstacles = {};

export function updatePoseCurrent(robot_id, new_pose) {
  pose_current[robot_id] = new_pose;
}

export function updatePoseOrder(robot_id, new_pose) {
  pose_order[robot_id] = new_pose;
}

export function recordPath(robot_id, msg) {
  path[robot_id] = msg;
}

export function updateObstacles(robot_id, new_obstacles) {
  obstacles[robot_id] = new_obstacles;
}

const robotImages = {};
const orderImages = {};
const robotColors = {
  1: "#F0A30A",
  2: "#3A5431",
  3: "#432D57",
  4: "#001DBC",
};

function loadImages() {
  for (let i = 1; i <= 4; i++) {
    robotImages[i] = new Image();
    orderImages[i] = new Image();
    robotImages[i].src = `static/img/robot${i}.png`;
    orderImages[i].src = `static/img/robot${i}.png`;
  }
}

loadImages();

function getImage(robot_id, type) {
  const images = type === "robot" ? robotImages : orderImages;
  return images[robot_id] || images[0];
}

let ratioX = null;
let ratioY = null;
let coordX = 0;
let coordY = 0;

function getFullHeight(className, includeMargin = true) {
  const element = document.querySelector(`.${className}`);
  if (!element) return 0;

  const styles = window.getComputedStyle(element);
  const height = element.offsetHeight;
  const margin = includeMargin
    ? parseFloat(styles.marginTop) + parseFloat(styles.marginBottom)
    : 0;

  return height + margin;
}

export function resizeCanvas() {
  const footerHeight = getFullHeight("footer", false);
  const navHeight = getFullHeight("nav-tabs", true);
  const menuWidth = document.getElementById("menu").offsetWidth;

  const canvas = document.getElementById("board");
  canvas.height = Math.min(
    window.innerHeight - (footerHeight + navHeight),
    document.getElementById("menu").offsetHeight
  );
  canvas.width = window.innerWidth - menuWidth - 10;

  const background = new Image();
  background.src = "static/img/ground2024.png";

  const imgWidth = canvas.width;
  const imgHeight = (imgWidth * 2) / 3;

  const adjustedHeight = imgHeight > canvas.height ? canvas.height : imgHeight;
  const adjustedWidth =
    adjustedHeight === canvas.height ? (adjustedHeight * 3) / 2 : imgWidth;

  const context = canvas.getContext("2d");
  context.canvas.width = adjustedWidth;
  context.canvas.height = adjustedHeight;

  coordX = 0;
  coordY = canvas.height / 2;
  context.translate(coordX, coordY);

  canvas.addEventListener("click", (event) => {
    console.log(getMousePos(canvas, event));
  });

  ratioX = adjustedWidth / 3000;
  ratioY = -adjustedHeight / 2000;

  setButtonPosition(canvas);
}

function setButtonPosition(canvas) {
  const rightPx = Math.max(
    window.innerWidth -
      document.getElementById("menu").offsetWidth -
      10 -
      canvas.width,
    0
  );
  document.getElementById("buttonRefresh").style.right = `${rightPx}px`;

  const buttonCameraModal = document.getElementById("buttonCameraModal");
  if (buttonCameraModal) {
    buttonCameraModal.style.top = canvas.height - 44 + "px"; // 44 is height of camera image
    buttonCameraModal.style.right = rightPx - 49 + "px"; // 49 is width of refresh image
  }
}

function getMousePos(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: event.clientX - rect.left - coordX,
    y: -(event.clientY - rect.top - coordY),
  };
}

export function displayMsg(robot_id, msg) {
  const stateHTML = document.getElementById(`state_robot_${robot_id}`);
  const pose = pose_current[robot_id];

  if (pose && !isNaN(pose.x) && !isNaN(pose.y)) {
    stateHTML.textContent = `R.${robot_id} Cy.:${
      msg.cycle
    } / X:${pose.x.toFixed(2)} / Y:${pose.y.toFixed(2)} / Ang:${pose.O.toFixed(
      2
    )}`;
  }
}

export function drawBoardElement() {
  const canvas = document.getElementById("board");
  const context = canvas.getContext("2d");

  function drawFrame() {
    context.clearRect(coordX, -coordY, canvas.width, canvas.height);

    for (const robot_id in pose_current) {
      const pose = pose_current[robot_id];
      if (pose && !isNaN(pose.x) && !isNaN(pose.y)) {
        drawRobot(getImage(robot_id, "robot"), pose.x, pose.y, pose.O, context);
      }

      const orderPose = pose_order[robot_id];
      if (orderPose) {
        context.save();
        context.filter = "opacity(60%)";
        drawRobot(
          getImage(robot_id, "order"),
          orderPose.x,
          orderPose.y,
          orderPose.O,
          context
        );
        context.restore();
      }

      const color = robotColors[robot_id] || "red";
      drawPathsAndObstacles(color, robot_id, context);
    }
    requestAnimationFrame(drawFrame);
  }

  requestAnimationFrame(drawFrame);
}

function drawPathsAndObstacles(color, robot_id, context) {
  const path_robot = path[robot_id] || [];
  const pose = pose_current[robot_id];

  if (pose) {
    if (path_robot.length > 0) {
      drawPath(color, pose, path_robot[0], context);
    }
    for (let i = 0; i < path_robot.length - 1; i++) {
      drawPath(color, path_robot[i], path_robot[i + 1], context);
    }
  }

  const obstacles_robot = obstacles[robot_id] || [];
  obstacles_robot.forEach((obstacle) => {
    drawObstacles(color, obstacle, context);
  });
}

function adaptCoords(x, y, angle) {
  return { x: 1500 - y, y: x, angle: -angle - 90 };
}

function drawRobot(robot, x, y, angle, context) {
  const { x: newX, y: newY, angle: newAngle } = adaptCoords(x, y, angle);
  const robotWidth = robot.width * ratioX;
  const robotHeight = robot.height * ratioY;

  context.save();
  context.translate(newX * ratioX, newY * ratioY);
  context.rotate((newAngle * Math.PI) / 180);
  context.drawImage(
    robot,
    -robotWidth / 2,
    -robotHeight / 2,
    robotWidth,
    robotHeight
  );
  context.restore();
}

function drawPath(color, start, end, context) {
  const startCoords = adaptCoords(start.x, start.y, 0);
  const endCoords = adaptCoords(end.x, end.y, 0);

  context.save();
  context.strokeStyle = color;
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(startCoords.x * ratioX, startCoords.y * ratioY);
  context.lineTo(endCoords.x * ratioX, endCoords.y * ratioY);
  context.stroke();
  context.restore();
}

function drawObstacles(color, obstacle, context) {
  const { x, y, angle } = adaptCoords(obstacle.x, obstacle.y, 0);
  const obstacleX = x * ratioX;
  const obstacleY = y * ratioY;

  context.save();
  context.fillStyle = obstacle.id ? "purple" : color;
  context.filter = "opacity(40%)";

  if (obstacle.radius) {
    context.beginPath();
    context.arc(obstacleX, obstacleY, obstacle.radius * ratioX, 0, 2 * Math.PI);
    context.fill();
    context.closePath();
  } else {
    context.translate(obstacleX, obstacleY);
    context.rotate((angle * Math.PI) / 180);
    context.fillRect(
      (-obstacle.length_x * ratioX) / 2,
      (-obstacle.length_y * ratioY) / 2,
      obstacle.length_x * ratioX,
      obstacle.length_y * ratioY
    );
  }

  context.restore();
}

// Event handler for hiding tab
function onHideTab(robot_id) {
  var iframe = document.getElementById(`robot${robot_id}-iframe`);
  iframe.removeAttribute("src");
}

// Event handler for showing tab
function onShowTab(robot_id) {
  var iframe = document.getElementById(`robot${robot_id}-iframe`);
  iframe.src = `http://robot${robot_id}:808${robot_id}`;
}

export function addNewTab(robot_id) {
  // Create new nav-tab element
  var newNavTab = document.createElement("li");
  newNavTab.className = "nav-item";
  newNavTab.innerHTML = `<button class="nav-link" id="robot${robot_id}-tab" data-bs-toggle="tab" data-bs-target="#robot${robot_id}" type="button" role="tab" aria-controls="robot${robot_id}" aria-selected="true">Robot ${robot_id}</button>`;

  // Create new tab-pane element
  var newTabPane = document.createElement("div");
  newTabPane.className = "tab-pane fade";
  newTabPane.id = `robot${robot_id}`;
  var navTabHeight = getFullHeight("nav-tabs", true);
  newTabPane.innerHTML = `<iframe id="robot${robot_id}-iframe" style="position: absolute; top: ${navTabHeight}px; bottom: 0; left: 0; right: 0; width: 100%; height: ${
    window.innerHeight - navTabHeight
  }px;" frameborder="0"></iframe>`;

  // Append new nav-tab to the nav-tabs container
  var navTabsContainer = document.querySelector(".nav-tabs");
  navTabsContainer.appendChild(newNavTab);

  // Append new tab-pane to the tab-content container
  var tabContentContainer = document.querySelector(".tab-content");
  tabContentContainer.appendChild(newTabPane);

  document
    .getElementById(`robot${robot_id}-tab`)
    .addEventListener("shown.bs.tab", function (e) {
      var robot_id = e.target.getAttribute("id").match(/robot(\d+)-tab/)[1];
      onShowTab(robot_id);
    });

  // Add event listener to newly created tab to unload the iframe when user leaves the tab
  document
    .getElementById(`robot${robot_id}-tab`)
    .addEventListener("hide.bs.tab", function (e) {
      // Get the ID of the unselected robot from the href attribute
      var robotId = e.target.getAttribute("id").match(/robot(\d+)-tab/)[1];
      onHideTab(robotId);
    });
}

export function deleteTab(robot_id) {
  // Select the new button element
  var navButton = document.getElementById(`robot${robot_id}-tab`);

  // Check if the tab to delete is active
  const deletedTabIsActive = navButton.classList.contains("active");

  // Select the new nav-item element
  var navTab = navButton.parentElement;

  // Select the new tab-pane element
  var tabPane = document.getElementById(`robot${robot_id}`);

  // Check if the elements exist before attempting to remove them
  if (navTab && tabPane) {
    // Remove the event listeners for the deleted tab
    navTab.removeEventListener("hide.bs.tab", onHideTab);
    navTab.removeEventListener("shown.bs.tab", onShowTab);

    // Remove the new nav-tab from the nav-tabs container
    var navTabsContainer = document.querySelector(".nav-tabs");
    navTabsContainer.removeChild(navTab);

    // Remove the new tab-pane from the tab-content container
    var tabContentContainer = document.querySelector(".tab-content");
    tabContentContainer.removeChild(tabPane);

    if (deletedTabIsActive) {
      // Activate beacon tab if the deleted tab was active
      var beaconButton = document.getElementById(`beacon-tab`);
      beaconButton.classList.add("active");
      var beaconPane = document.getElementById(`beacon`);
      beaconPane.classList.add("active", "show");
    }
  }
}

export function deleteTabs() {
  document.querySelectorAll('[id^="robot"][id$="-tab"]').forEach(function (x) {
    const match = x.id.match(/robot(\d+)-tab/);
    if (match) {
      deleteTab(parseInt(match[1], 10));
    }
  });
}
