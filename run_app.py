#!/bin/env python
from lsapp import create_app

app = create_app()
if __name__ == '__main__':
    app.run() #production code