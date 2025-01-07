# Overview

This repository provides all Python tools developed by the COGIP robotic team.
The team is developing a robot for [Eurobot](https://www.eurobot.org/), French robotic contest.

All the tools are used during the game itself, or for development, debugging and monitoring of the robot and other test platforms.

## Robot Software Architecture

The main components of the robot are:

  - a STM32 that runs [`mcu-firmware`](https://github.com/cogip/mcu-firmware),
  - a Raspberry Pi 4 that controls a camera, a touchscreen and a Lidar.

The robot is associated with a central beacon having an upper view of the game area,
composed of a Raspberry Pi 4, a camera and a touchscreen.

![Robot Architecture Overview](img/cogip-overview-stm32.svg)

Tools running on the robot's Raspberry Pi 4 are:

  - [`Server`](usage/server.md) connecting all components through a SocketIO server.
  - [`Dashboard`](usage/dashboard.md) a web server providing a dashboard to control and monitor the robot.
  - [`Planner`](usage/planner.md) in charge of the game strategy.
  - [`Copilot`](usage/copilot.md) driving the robot moves by communicating
    with `mcu-firmware` (on STM32) using Protobuf messages over a serial port.
  - [`Detector`](usage/detector.md) generating obstacles based on Lidar data.
  - [`Robotcam`](usage/robotcam.md) reading and analyzing images from the camera.

Tools running on the central beacon's Raspberry Pi 4 are:

  - [`Server Beacon`](usage/server_beacon.md) connecting all beacon components through a SocketIO server,
  and connected to the SocketIO server of all robots.
    It also runs a web server providing a `Dashboard` to control and monitor the robot.
  - [`Dashboard`](usage/dashboard.md), a web server providing a dashboard to control and monitor the beacon, and display the dashboard of all robots.
  - [`Beaconcam`](usage/beaconcam.md) reading and analyzing images of the game area from the camera.

!!! warning "Beacon services will be redesigned and are not yet available. Robots can run standalone."

[`Monitor`](usage/monitor.md) is running on a PC connected to the SocketIO server.

[`Camera`](usage/camera.md) provides different commands to get information about cameras,
calibrate them and detect Aruco tags.

The touchscreens display the `Dashboard` using an web browser embedded in the Raspberry Pi.

## Emulation Software Architecture

During development, an emulation environment is also available. In this case,
all robot and beacon components are running on the development PC.

![Emulation Architecture Overview](img/cogip-overview-emulation.svg)

In this mode, fake Lidar data are provided by the `Monitor`.
