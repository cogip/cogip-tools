#!/bin/bash

/usr/bin/chromium-browser http://localhost:808ROBOT_ID \
    --no-sandbox \
    --disable-setuid-sandbox \
    --enable-features=UseOzonePlatform \
    --ozone-platform=wayland \
    --kiosk \
    --disable-infobars \
    --disable-extensions \
    --disable-pinch \
    --remote-debugging-port=9222
