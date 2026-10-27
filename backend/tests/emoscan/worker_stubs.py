"""Synthetic child-process targets, not production expression predictions."""
import time


def ready(connection, frame, model_path):
    connection.send({'status': 'READY', 'synthetic_test_pixel': int(frame[0, 0, 0])})
    connection.close()


def hang(connection, frame, model_path):
    time.sleep(60)


def crash(connection, frame, model_path):
    connection.close()
