"""Application entry point."""

import sys

from .application import Application
from .exceptions import VkinderError
from .log import get_colored_traceback
from .log import get_logger
from .log import setup_loging


def main():
    """Initialize the bot and run it."""
    setup_loging()
    logger = get_logger(main)
    logger.info('Application started')
    try:
        app = Application()
        app.run()
    except KeyboardInterrupt:
        logger.info('Stopped by keyboard interrupt')
    except VkinderError as e:
        logger.critical('Stopped on error: %s', e)
        logger.debug('Exception info:\n%s', get_colored_traceback())
        sys.exit(1)


if __name__ == '__main__':
    main()
