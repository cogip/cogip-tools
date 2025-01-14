# Server

The `Server` tool is running on the Raspberry Pi embedded in a robot.

It implements a Socket.IO server on which all other tools from robot and central beacon
are connected on their own namespace.
This server is only used to redirect messages from a tool to another.

The Socket.IO server listen on port `8090 + robot_id`, ie `8091` on robot 1.

## Run Server

```bash
$ cogip-server
```

## Parameters

`Server` default parameters can be modified using command line options or environment variables:

```bash
$ cogip-server --help
Usage: cogip-server [OPTIONS]

  --id , -i INTEGER RANGE         Robot ID
                                  env var: ROBOT_ID, SERVER_ID
                                  default: 0; 0<=x<=9

  --dashboard_update_interval FLOAT RANGE
                                  Interval between messages to dashboard (in seconds)
                                  env var: SERVER_DASHBOARD_UPDATE_INTERVAL
                                  default: 0.2

  --record-dir PATH               Directory where games will be recorded
                                  env var: SERVER_RECORD_DIR
                                  default: /var/tmp/cogip

  -r, --reload                    Reload app on source file changes
                                  env var: COGIP_RELOAD, PLANNER_RELOAD

  -d, --debug                     Turn on debug messages
                                  env var: COGIP_DEBUG, PLANNER_DEBUG
```
