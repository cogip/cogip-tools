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
  // Just record path.
  // It is updated on board each time drawBoardElement() is called (on state reception).
  path[robot_id] = msg;
}

export function updateObstacles(robot_id, new_obstacles) {
  obstacles[robot_id] = new_obstacles;
}

let img_robot = new Image();
img_robot.src = "static/img/robot.png";
let img_robot1 = new Image();
img_robot1.src = "static/img/robot1.png";
let img_robot2 = new Image();
img_robot2.src = "static/img/robot2.png";
let img_robot3 = new Image();
img_robot3.src = "static/img/robot3.png";
let img_robot4 = new Image();
img_robot4.src = "static/img/robot4.png";

let order_robot = new Image();
order_robot.src = "static/img/robot.png";
let order_robot1 = new Image();
order_robot1.src = "static/img/robot1.png";
let order_robot2 = new Image();
order_robot2.src = "static/img/robot2.png";
let order_robot3 = new Image();
order_robot3.src = "static/img/robot3.png";
let order_robot4 = new Image();
order_robot4.src = "static/img/robot4.png";

function getImageRobot(robot_id) {
  switch (robot_id) {
    case "1":
      return img_robot1;
    case "2":
      return img_robot2;
    case "3":
      return img_robot3;
    case "4":
      return img_robot4;
  }
  return img_robot;
}

function getImageOrder(robot_id) {
  switch (robot_id) {
    case "1":
      return order_robot1;
    case "2":
      return order_robot2;
    case "3":
      return order_robot3;
    case "4":
      return order_robot4;
  }
  return order_robot;
}

/*
1. F0A30A F0A30A
2. 6D8764 3A5431
3. 76608A 432D57
4. 0050EF 001DBC
*/

function getRobotColor(robot_id) {
  switch (robot_id) {
    case "1":
      return "#F0A30A";
    case "2":
      return "#3A5431";
    case "3":
      return "#432D57";
    case "4":
      return "#001DBC";
  }
  return "red";
}

let ratioX = null;
let ratioY = null;
let coordX = 0;
let coordY = 0;

function getFullHeight(className, includeMargin = true) {
  const footer = document.getElementsByClassName(className)[0];

  if (!footer) {
    return 0
  }

  const footerStyles = window.getComputedStyle(footer);

  const footerHeightWithPadding = footer.offsetHeight;
  let footerMarginTop = 0;
  let footerMarginBottom = 0;

  if (includeMargin) {
    footerMarginTop = parseFloat(footerStyles.marginTop);
    footerMarginBottom = parseFloat(footerStyles.marginBottom);
  }

  return footerHeightWithPadding + footerMarginTop + footerMarginBottom;
}

export function resizeCanvas() {
  const footerHeight = getFullHeight("footer", false);
  const navHeight = getFullHeight("nav-tabs", true);
  const menuWidth = document.getElementById("menu").offsetWidth;

  let htmlCanvas = document.getElementById("board");

  htmlCanvas.height = Math.min(
    window.innerHeight - (footerHeight + navHeight),
    document.getElementById("menu").offsetHeight
  );

  htmlCanvas.width = window.innerWidth - menuWidth - 10;

  let background = new Image();
  background.src = "static/img/ground2024.png"; // default background size 2000x3000 --> ratio 2/3

  let imgWidth = htmlCanvas.width;
  let imgHeight = (imgWidth * 2) / 3;

  if (imgHeight > htmlCanvas.height) {
    imgHeight = htmlCanvas.height;
    imgWidth = (imgHeight * 3) / 2;
  }

  const context = htmlCanvas.getContext("2d");

  context.canvas.width = imgWidth;
  context.canvas.height = imgHeight;

  coordX = 0;
  coordY = htmlCanvas.height / 2;

  context.translate(coordX, coordY); // x invert

  htmlCanvas.addEventListener("click", function (event) {
    console.log(getMousePos(this, event));
  });

  ratioX = imgWidth / 3000;
  ratioY = -imgHeight / 2000;

  setButtonPosition(htmlCanvas);
}

function setButtonPosition(htmlCanvas) {
  // set right of buttons Camera and Refresh
  const rightPx = Math.max(
    window.innerWidth -
      document.getElementById("menu").offsetWidth -
      10 -
      htmlCanvas.width,
    0
  );

  document.getElementById("buttonRefresh").style.right = rightPx + "px";
}

function getMousePos(canvas, evt) {
  let transX = coordX;
  let transY = coordY;
  let rect = canvas.getBoundingClientRect();
  return {
    x: evt.clientX - rect.left - transX,
    y: -(evt.clientY - rect.top - transY),
  };
}

export function displayMsg(robot_id, msg) {
  let stateHTML = document.getElementById(`state_robot_${robot_id}`);

  let pose_current_robot = pose_current[robot_id];

  if (
    pose_current_robot !== undefined &&
    !isNaN(pose_current_robot.x) &&
    !isNaN(pose_current_robot.y)
  ) {
    stateHTML.textContent = `R.${robot_id} Cy.:${
      msg.cycle
    } / X:${pose_current_robot.x.toFixed(2)} / Y:${pose_current_robot.y.toFixed(
      2
    )} / Ang:${pose_current_robot.O.toFixed(2)}`;
  }
}

export function drawBoardElement(msg) {
  // get board dom element
  let htmlCanvas = document.getElementById("board");
  const context = htmlCanvas.getContext("2d");

  // clear area
  context.clearRect(coordX, -coordY, htmlCanvas.width, htmlCanvas.height);

  // draw robot
  // init robot position
  for (let robot_id in pose_current) {
    let pose_current_robot = pose_current[robot_id];
    if (
      pose_current_robot !== undefined &&
      !isNaN(pose_current_robot.x) &&
      !isNaN(pose_current_robot.y)
    ) {
      const robotX = pose_current_robot.x;
      const robotY = pose_current_robot.y;
      const robotO = pose_current_robot.O;
      drawRobot(getImageRobot(robot_id), robotX, robotY, robotO, context);
    }

    // draw order
    let pose_order_robot = pose_order[robot_id];
    if (pose_order_robot !== undefined) {
      context.save();
      context.filter = "opacity(60%)";
      drawRobot(
        getImageOrder(robot_id),
        pose_order_robot.x,
        pose_order_robot.y,
        pose_order_robot.O,
        context
      );
      context.restore();
    }

    const robot_color = getRobotColor(robot_id);

    // draw path
    let path_robot = path[robot_id] ?? Array();
    if (path_robot.length > 0 && pose_current_robot !== undefined) {
      drawPath(robot_color, pose_current_robot, path_robot[0], context);
    }
    for (let i = 0; i < path_robot.length - 1; i++) {
      const startPoint = path_robot[i];
      const endPoint = path_robot[i + 1];
      drawPath(robot_color, startPoint, endPoint, context);
    }

    // draw obstacles
    let obstacles_robot = obstacles[robot_id] ?? Array();
    if (obstacles_robot.length) {
      obstacles_robot.forEach(function (obstacle) {
        drawObstacles(robot_color, obstacle, context);
      });
    }
  }
}

function adaptCoords(x, y, angle) {
  const newX = 1500 - y;
  const newY = x;
  const newAngle = -angle - 90;
  return { newX, newY, newAngle };
}

function drawRobot(robot, x, y, O, context) {
  let robotWidth = robot.width * ratioX;
  let robotHeight = robot.height * ratioY;

  const { newX, newY, newAngle } = adaptCoords(x, y, O);

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

function drawPath(color, startPoint, endPoint, context) {
  const {
    newX: newStartX,
    newY: newStartY,
    newAngle: newStartAngle,
  } = adaptCoords(startPoint.x, startPoint.y, 0);
  const {
    newX: newEndX,
    newY: newEndY,
    newAngle: newEndAngle,
  } = adaptCoords(endPoint.x, endPoint.y, 0);

  context.save();
  context.strokeStyle = color;
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(newStartX * ratioX, newStartY * ratioY);
  context.lineTo(newEndX * ratioX, newEndY * ratioY);
  context.closePath();
  context.stroke();
  context.restore();
}

function drawObstacles(color, obstacle, context) {
  const { newX, newY, newAngle } = adaptCoords(obstacle.x, obstacle.y, 0);
  let obstacleX = newX * ratioX;
  let obstacleY = newY * ratioY;

  context.save();
  if (obstacle.id) {
    // Fixed obstacles: they have an id in case of artefact, or length_x in case of rectangle.
    context.fillStyle = "purple";
  } else {
    // Other obstacles are dynamic obstacles and of circle shape.
    context.fillStyle = color;
  }
  context.filter = "opacity(40%)";

  if (obstacle.radius) {
    let radius = obstacle.radius * ratioX;

    context.beginPath();
    context.arc(obstacleX, obstacleY, radius, 0, 2 * Math.PI);
    context.fill();
    context.closePath();
  } else {
    let length_x = obstacle.length_x * ratioX;
    let length_y = obstacle.length_y * ratioY;

    context.translate(obstacleX, obstacleY);
    context.rotate((newAngle * Math.PI) / 180);
    context.fillRect(-length_x / 2, -length_y / 2, length_x, length_y);
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
