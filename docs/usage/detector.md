# Detector

The `Detector` tool is running on the Raspberry Pi embedded in the robot.

It communicates on the `/detector` namespace of the SocketIO server
running on the central beacon over Wifi.

It builds dynamic obstacles used by `Monitor`/`Dashboards` for display
and by `mcu-firmware` to compute avoidance path.

`Detector` can operate in monitoring or emulation mode.

### Monitoring Mode

Read data from lidar connected on a serial port of the Raspberry Pi.
This is the default mode when a Lidar is connected, since the YDLidar SDK automatically
detects the serial port to use.

### Emulation Mode

Ask the `Monitor` to emulate the Lidar which sends its data through the SocketIO server.
The emulation mode is enabled if no Lidar is detected at startup.
In case of a false detection, use the `--emulation` option.

## Data Flow

![Detector Data Flow](../img/cogip-detector.svg)

## Run Detector

```bash
$ cogip-detector
```

## Parameters

`Detector` default parameters can be modified using command line options or environment variables:

```
$ cogip-detector --help
Usage: cogip-detector [OPTIONS]

Options:
  -i, --robot-id INTEGER RANGE    Robot ID.
                                  env var: ROBOT_ID, DETECTOR_ID
                                  default: 1; x>=1

  --server-url TEXT               Socket.IO Server URL
                                  env var: COGIP_SOCKETIO_SERVER_URL
                                  default: None

  -p, --lidar-port PATH           Serial port connected to the Lidar
                                  env var: DETECTOR_LIDAR_PORT
                                  default: None (autodetect)

  --min-distance INTEGER          Minimum distance to detect an obstacle
                                  env var: DETECTOR_MIN_DISTANCE
                                  default: 150

  --max-distance INTEGER          Maximum distance to detect an obstacle
                                  env var: DETECTOR_MAX_DISTANCE
                                  default: 2500

  --min-intensity INTEGER         Minimum intensity to detect an obstacle
                                  env var: DETECTOR_MIN_INTENSITY
                                  default: 0; x>=1; x<=255

  --refresh-interval FLOAT        Interval between each update of the obstacle list (in seconds)
                                  env var: DETECTOR_REFRESH_INTERVAL
                                  default: 0.1; x>=-1.0; x<=2.0

  --sensor-delay INTEGER          Delay to compensate the delay between sensor data fetch and obstacle positions computation.
                                  Unit is the index of pose current to get in the past
                                  env var: DETECTOR_SENSOR_DELAY
                                  default: 0; x>=0; x<=100

  --cluster-min-samples INTEGER RANGE
                                  Minimum number of samples to form a cluster
                                  env var: DETECTOR_CLUSTER_MIN_SAMPLES
                                  default: 4; 1<=x<=20

  --cluster-eps FLOAT RANGE       Maximum distance between two samples to form a cluster (mm)
                                  env var: DETECTOR_CLUSTER_EPS
                                  default: 40.0; 1.0<=x<=100.0

  -g, --gui                       Launch the GUI.
                                  env var: DETECTOR_GUI

  -w, --web                       Launch the web server.
                                  env var: DETECTOR_WEB

  -r, --reload                    Reload app on source file changes.
                                  env var: COGIP_RELOAD, DETECTOR_RELOAD

  -d, --debug                     Turn on debug messages.
                                  env var: COGIP_DEBUG, DETECTOR_DEBUG
```
