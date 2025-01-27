import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(name)s][%(threadName)s] %(levelname)s: %(message)s")

logger = logging.getLogger(__name__)
