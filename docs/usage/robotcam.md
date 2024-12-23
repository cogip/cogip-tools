# RobotCam

The `RobotCam` tool is running on the Raspberry Pi embedded in the robot.

It communicates on the `/robotcam` namespace of the SocketIO server
running on the central beacon over Wifi.

It handles the robot camera, detect game elements using Aruco markers and stream the video to a web server.

The web server listen on port `8100 + robot_id`, ie `8100` on the beacon or `8101` on robot 1.

## Run RobotCam

```bash
$ cogip-robocam
```

## Parameters

RobotCam default parameters can be modified using environment variables.
All variables can be defined in the `.env` file.

Example of `.env` file with all default values:

```bash
# Socket.IO Server URL
COGIP_SOCKETIO_SERVER_URL="http://localhost:8091"

# Robot ID
ROBOTCAM_ID=1

# Camera name
ROBOTCAM_CAMERA_NAME="hbv"

# Camera frame width
ROBOTCAM_CAMERA_WIDTH=640

# Camera frame height
ROBOTCAM_CAMERA_HEIGHT=480

# Camera video codec
ROBOTCAM_CAMERA_CODEC="yuyv"

# Number of uvicorn workers (ignored if launched by gunicorn)
ROBOTCAM_NB_WORKERS=1

# Size of the shared memory storing the last frame to stream on server
# (size for a frame in BMP format, black and white, 640x480 pixels)
ROBOTCAM_FRAME_SIZE=308316
```
