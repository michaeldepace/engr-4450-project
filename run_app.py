from lsapp import create_app

# trigger application start from deployment server
app = create_app() 
if __name__ == '__main__':
    app.run() # run application from __init__.py