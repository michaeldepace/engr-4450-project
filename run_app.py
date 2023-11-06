#!/bin/env python
from lsapp import create_app, socketio

app = create_app()
if __name__ == '__main__':
    socketio.run(app) #deployment code
    #app.run() #production code