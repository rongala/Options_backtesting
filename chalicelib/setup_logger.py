import logging


def get_logger(app_name):
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-3s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)
    logger = logging.getLogger(app_name)
    return logger
