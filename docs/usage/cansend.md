# cansend

Helper tool to send CAN command on a CAN bus using COGIP messages.

Use `--help` argument to show available commands:

```bash
$ cogip-cansend --help
Usage: cogip-cansend [OPTIONS]

Options:
  -c, --can-channel TEXT      CAN channel connected to STM32 modules
                              env var: CANSEND_CAN_CHANNEL
                              default: vcan0

  -b, --can-bitrate INTEGER   CAN bitrate
                              env var: CANSEND_CAN_BITRATE
                              default: 500000

  -B, --data-bitrate INTEGER  CAN FD data bitrate
                              env var: CANSEND_CANFD_DATA_BITRATE
                              default: 1000000

  -c, --commands FILENAME     YAML file containing
                              env var: CANSEND_COMMANDS
                              default: 1000000

  --help                      Show this message and exit.
```

The list of commands to send is provided using a YAML file.

The commands are defined in `cogip/models/actuators.py`,
like [PositionalActuatorCommand][cogip.models.actuators.PositionalActuatorCommand].

Enum attributes can be specified by their name or value.

Example:

```yaml
- kind: 0
  id: LXSERVO_LEFT_CART
  command: 100

- kind: POSITIONAL
  id: 2
  command: 1
```
