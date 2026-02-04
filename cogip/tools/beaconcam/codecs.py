from enum import StrEnum


class VideoCodec(StrEnum):
    """Video codecs supported by our cameras"""

    mjpg = "MJPG"
    yuyv = "YUYV"
