# Camera

The `Camera` tool provides different commands to get information about cameras,
calibrate them and detect Aruco tags.

Use `--help` argument to show available commands:

```bash
$ cogip-camera --help
Usage: cogip-camera [OPTIONS] COMMAND [ARGS]...

Options:
  -d, --debug           Turn on debug messages
                        env var: COGIP_DEBUG, CAMERA_DEBUG

  --help                Show this message and exit.

Commands:
  calibrate  Calibrate camera using images captured by the 'capture' command
  capture    Capture images to be used by the 'calibrate' command
  charuco    Display charuco board to check if is corresponds to the board used for calibration
  detect     Detect Aruco tags and estimate their positions
  info       Get properties of connected cameras
```

## Info Command

Display properties of connected cameras.

If a camera name is provided, only display properties of this camera
and preview its video stream.
Codec, width and height arguments apply only in this context.


```bash
$ cogip-camera info --help
Usage: cogip-camera info [OPTIONS]

  Get properties of connected cameras

Options:
  -i, --id INTEGER RANGE          Robot ID.
                                  env var: ROBOT_ID, CAMERA_ID
                                  default: 1, x>=0

  --camera-name [hbv|sonix]   Name of the camera (all if not specified)
                              env var: CAMERA_NAME

  --camera-codec [mjpg|yuyv]  Camera video codec
                              env var: CAMERA_CODEC
                              default: yuyv

  --camera-width INTEGER      Camera frame width
                              env var: CAMERA_WIDTH
                              default: 1920

  --camera-height INTEGER     Camera frame height
                              env var: CAMERA_HEIGHT
                              default: 1080

  --help                      Show this message and exit.
```

## Charuco Command

Display charuco board to check if is corresponds to the board used for calibration.
Same parameters must be used with the `capture` and `calibrate` commands.

```bash
$ cogip-camera charuco --help
Usage: cogip-camera charuco [OPTIONS]

  Display charuco board to check if is corresponds to the board used for calibration

Options:
  --charuco-rows INTEGER          Number of rows on the Charuco board
                                  env var: CAMERA_CHARUCO_ROWS
                                  default: 8

  --charuco-cols INTEGER          Number of columns on the Charuco board
                                  env var: CAMERA_CHARUCO_COLS
                                  default: 13

  --charuco-marker-length INTEGER
                                  Length of an Aruco marker on the Charuco board (in mm)
                                  env var: CAMERA_CHARUCO_MARKER_LENGTH
                                  default: 23

  --charuco-square-length INTEGER
                                  Length of a square in the Charuco board (in mm)
                                  env var: CAMERA_CHARUCO_SQUARE_LENGTH
                                  default: 30

  --charuco-legacy / --no-charuco-legacy
                                  Use Charuco boards compatible with OpenCV < 4.6
                                  env var: CAMERA_CHARUCO_LEGACY
                                  default: no-charuco-legacy

  --help                          Show this message and exit.
```

## Capture Command

Capture images to be used by the `calibrate` command.

Use `--max-frames` and `--capture-interval` options to customize
the number of images to capture and the frequency of capture.

To be valid for calibration, the images must contained a charuco board
with different orientations on each image. Use `--charuco-*` options to configure
the Charuco board used for calibration.

The captured images will be displayed after charuco board detection.

The Charuco board generated for detection is also displayed for comparison with the board on images.

Images are stored in `cameras/<robot_id>/<camera_name>_<camera_codec>_<camera_width>x<camera_height>/images`.

```bash
$ cogip-camera capture --help
Usage: cogip-camera capture [OPTIONS]

  Capture images to be used by the 'calibrate' command

Options:
  -i, --id INTEGER RANGE          Robot ID.
                                  env var: ROBOT_ID, CAMERA_ID
                                  default: 1, x>=0

  --camera-name [hbv|sonix]       Name of the camera
                                  env var: CAMERA_NAME
                                  default: hbv

  --camera-codec [mjpg|yuyv]      Camera video codec
                                  env var: CAMERA_CODEC
                                  default: yuyv

  --camera-width INTEGER          Camera frame width
                                  env var: CAMERA_WIDTH
                                  default: 1920

  --camera-height INTEGER         Camera frame height
                                  env var: CAMERA_HEIGHT
                                  default: 1080

  --max-frames INTEGER            Maximum number of frames to read before exiting
                                  env var: CAMERA_MAX_FRAMES
                                  default: 120

  --capture-interval INTEGER      Capture an image every 'capture_interval' frames
                                  env var: CAMERA_CAPTURE_INTERVAL
                                  default: 10

  --charuco-rows INTEGER          Number of rows on the Charuco board
                                  env var: CAMERA_CHARUCO_ROWS
                                  default: 8

  --charuco-cols INTEGER          Number of columns on the Charuco board
                                  env var: CAMERA_CHARUCO_COLS
                                  default: 13

  --charuco-marker-length INTEGER
                                  Length of an Aruco marker on the Charuco board (in mm)
                                  env var: CAMERA_CHARUCO_MARKER_LENGTH
                                  default: 23

  --charuco-square-length INTEGER
                                  Length of a square in the Charuco board (in mm)
                                  env var: CAMERA_CHARUCO_SQUARE_LENGTH
                                  default: 30

  --charuco-legacy / --no-charuco-legacy
                                  Use Charuco boards compatible with OpenCV < 4.6
                                  env var: CAMERA_CHARUCO_LEGACY
                                  default: charuco-legacy

  --help                          Show this message and exit.
```

## Calibrate Command

Generate intrinsic calibration parameters using images recorded by the `capture` command.

The parameter file is written in `cameras/<robot_id>/<camera_name>_<camera_codec>_<camera_width>x<camera_height>/params.yaml`.

```bash
$ cogip-camera calibrate --help
Usage: cogip-camera calibrate [OPTIONS]

  Calibrate camera using images captured by the 'capture' command

Options:
  -i, --id INTEGER RANGE          Robot ID.
                                  env var: ROBOT_ID, CAMERA_ID
                                  default: 1, x>=0

  --camera-name [hbv|sonix]       Name of the camera
                                  env var: CAMERA_NAME
                                  default: hbv

  --camera-codec [mjpg|yuyv]      Camera video codec
                                  env var: CAMERA_CODEC
                                  default: yuyv

  --camera-width INTEGER          Camera frame width
                                  env var: CAMERA_WIDTH
                                  default: 1920

  --camera-height INTEGER         Camera frame height
                                  env var: CAMERA_HEIGHT
                                  default: 1080

  --charuco-rows INTEGER          Number of rows on the Charuco board
                                  env var: CAMERA_CHARUCO_ROWS
                                  default: 8

  --charuco-cols INTEGER          Number of columns on the Charuco board
                                  env var: CAMERA_CHARUCO_COLS
                                  default: 13

  --charuco-marker-length INTEGER
                                  Length of an Aruco marker on the Charuco board (in mm)
                                  env var: CAMERA_CHARUCO_MARKER_LENGTH
                                  default: 23

  --charuco-square-length INTEGER
                                  Length of a square in the Charuco board (in mm)
                                  env var: CAMERA_CHARUCO_SQUARE_LENGTH
                                  default: 30

  --charuco-legacy / --no-charuco-legacy
                                  Use Charuco boards compatible with OpenCV < 4.6
                                  env var: CAMERA_CHARUCO_LEGACY
                                  default: charuco-legacy

  --help                          Show this message and exit.
```

## Detect Command

Detect Aruco tags and estimate their positions.

```bash
$ cogip-camera detect --help
Usage: cogip-camera detect [OPTIONS]

  Detect Aruco tags and estimate their positions

Options:
  -i, --id INTEGER RANGE          Robot ID.
                                  env var: ROBOT_ID, CAMERA_ID
                                  default: 1, x>=0

  --camera-name [hbv|sonix]       Name of the camera
                                  env var: CAMERA_NAME
                                  default: hbv

  --camera-codec [mjpg|yuyv]      Camera video codec
                                  env var: CAMERA_CODEC
                                  default: yuyv

  --camera-width INTEGER          Camera frame width
                                  env var: CAMERA_WIDTH
                                  default: 1920

  --camera-height INTEGER         Camera frame height
                                  env var: CAMERA_HEIGHT
                                  default: 1080

  --robot-position INTEGER        Define the robot position
                                  env var: CAMERA_ROBOT_POSITION

  --help                          Show this message and exit.
```
