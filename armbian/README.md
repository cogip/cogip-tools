# Armbian images for COGIP

Migration of the `raspios/` image pipeline to Armbian, using the vendor kernel
shipped by Armbian (no mainline kernel build).

## Phases

- **board-probe-img/**: board feasibility probe. Build a minimal Armbian image for a
  given board (`BOARD=rpi4b`, `BOARD=rock-5b`, ...), boot it root-only with no
  wizard, and have it write a hardware report (CAN/I2C/SPI/UART/camera/GPIO) to
  the boot partition. Reusable to qualify any new board before porting COGIP.
- **board-cogip-img/**: the real COGIP image, port of `raspios/`. Built in steps:
  (1) base + peripherals [done], (2) COGIP app, (3) targets beacon/robot/pami,
  (4) per-robot images. See its README.

The kernel strategy is: never rebuild the kernel if avoidable. Prefer loadable
modules (`modules-load.d`) and device-tree overlays. Only add a kernel config
fragment as a last resort, for an option absent even as a module. Phase 0 is
what tells us, per board, whether that last resort is needed.
