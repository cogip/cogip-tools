if [ -z $DISPLAY ] && [ $(tty) = /dev/tty1 -o $(tty) = /dev/console ]
then
  weston --backend=drm-backend.so
fi
