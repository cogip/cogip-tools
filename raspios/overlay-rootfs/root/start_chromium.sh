#!/bin/bash

/usr/bin/chromium-browser http://localhost:8080 \
    --no-sandbox \
    --disable-setuid-sandbox \
    --enable-features=UseOzonePlatform \
    --ozone-platform=wayland \
    --kiosk \
    --incognito \
    --disable-infobars \
    --disable-extensions \
    --disable-pinch \
    --disable-translate \
    --disable-features=TranslateUI \
    --overscroll-history-navigation=0 \
    --noerrdialogs \
    --disk-cache-dir=/dev/null \
    --remote-debugging-port=9222
