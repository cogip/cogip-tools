import sys

from cogip.utils.logger import Logger

logger = Logger("cogip-camera", enable_cpp=False)

# Give access to system site-packages to find libcamera installed by apt
sys.path.append("/usr/lib/python3/dist-packages")
