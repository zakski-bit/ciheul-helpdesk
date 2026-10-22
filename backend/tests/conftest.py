import sys

def pytest_unconfigure(config):
    sys.stdout.flush()
    sys.stderr.flush()
