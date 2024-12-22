let pose_current = undefined;
let pose_order = undefined;
let path = [];
let obstacles = [];
let robot = new Image();
let order = new Image();

const ROBOT_IMAGES = {
  1: "static/img/robot.png",
  2: "static/img/pami.png",
};

function setRobotImage(imageObj, robotId) {
  if (imageObj.src === "") {
    imageObj.src = ROBOT_IMAGES[robotId] || ROBOT_IMAGES[2]; // Default to second image if robotId is not found
  }
}

export function updatePoseCurrent(robot_id, new_pose) {
  setRobotImage(robot, robot_id);
  pose_current = new_pose;
}

export function updatePoseOrder(robot_id, new_pose) {
  setRobotImage(order, robot_id);
  pose_order = new_pose;
}

export function recordPath( msg) {
  // Just record path.
  // It is updated on board each time drawBoardElement() is called (on state reception).
  path = msg;
}

export function updateObstacles(new_obstacles) {
  obstacles = new_obstacles;
}

let ratioX = null;
let ratioY = null;
let coordX = 0;
let coordY = 0;

export function resizeCanvas() {
  const footerHeight =
    document.getElementsByTagName("footer")[0].offsetHeight;
  const menuWidth = document.getElementById("menu").offsetWidth;

  let htmlCanvas = document.getElementById("board");

  htmlCanvas.height = Math.min(
    window.innerHeight - footerHeight,
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
  // set top of buttonCameraModal
  const buttonCameraModal = document.getElementById("buttonCameraModal");
  buttonCameraModal.style.top = buttonCameraModal.style.top =
    htmlCanvas.height - 44 + "px"; // 44 is height of camera image

  // set right of buttons Camera and Refresh
  const rightPx = Math.max(
    window.innerWidth -
      document.getElementById("menu").offsetWidth -
      htmlCanvas.width,
    0
  );

  document.getElementById("buttonRefresh").style.right = rightPx + "px";
  buttonCameraModal.style.right = rightPx - 59 + "px"; // 49 is width of refresh image
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

export function displayMsg(msg) {
  let stateHTML = document.getElementById("state_robot");

  let pose_current_robot = pose_current;

  if (
    pose_current_robot !== undefined &&
    !isNaN(pose_current_robot.x) &&
    !isNaN(pose_current_robot.y)
  ) {
    stateHTML.textContent = `R Cy.:${
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
  if (
    pose_current !== undefined &&
    !isNaN(pose_current.x) &&
    !isNaN(pose_current.y)
  ) {
    const robotX = pose_current.x;
    const robotY = pose_current.y;
    const robotO = pose_current.O;
    drawRobot(robotX, robotY, robotO, context);
  }

  // draw order
  if (pose_order !== undefined) {
    context.save();
    context.filter = "opacity(60%)";
    drawRobot(
      pose_order.x,
      pose_order.y,
      pose_order.O,
      context
    );
    context.restore();
  }

  // draw path
  let path_robot = path;
  if (path_robot.length > 0 && pose_current !== undefined) {
    drawPath(pose_current, path_robot[0], context);
  }
  for (let i = 0; i < path_robot.length - 1; i++) {
    const startPoint = path_robot[i];
    const endPoint = path_robot[i + 1];

    drawPath(startPoint, endPoint, context);
  }

  // draw obstacles
  if (obstacles.length) {
    obstacles.forEach(function (obstacle) {
      drawObstacles(obstacle, context);
    });
  }
}

function adaptCoords(x, y, angle) {
  const newX = 1500 - y;
  const newY = x;
  const newAngle = -angle - 90;
  return { newX, newY, newAngle };
}

function drawRobot(x, y, O, context) {
  let robotWidth = robot.width * ratioX;
  let robotHeight = robot.height * ratioY;

  const { newX, newY, newAngle } = adaptCoords(x, y, O)

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

function drawPath(startPoint, endPoint, context) {
  const { newX: newStartX, newY: newStartY, newAngle: newStartAngle } = adaptCoords(startPoint.x, startPoint.y, 0)
  const { newX: newEndX, newY: newEndY, newAngle: newEndAngle } = adaptCoords(endPoint.x, endPoint.y, 0)

  context.save();
  context.strokeStyle = "blue";
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(newStartX * ratioX, newStartY * ratioY);
  context.lineTo(newEndX * ratioX, newEndY * ratioY);
  context.closePath();
  context.stroke();
  context.restore();
}

function drawObstacles(obstacle, context) {
  const { newX, newY, newAngle } = adaptCoords(obstacle.x, obstacle.y, obstacle.angle)
  let obstacleX = newX * ratioX;
  let obstacleY = newY * ratioY;

  context.save();
  if (obstacle.id || obstacle.length_x) {
    // Fixed obstacles: they have an id in case of artefact, or length_x in case of rectangle.
    context.fillStyle = "purple";
  }
  else {
    // Other obstacles are dynamic obstacles and of circle shape.
    context.fillStyle = "red";
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
    context.rotate(newAngle * Math.PI / 180);
    context.fillRect(-length_x / 2, -length_y / 2, length_x, length_y);
  }

  context.restore();
}
