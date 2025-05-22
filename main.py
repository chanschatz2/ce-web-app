from website import create_app # we can do this bc /website is a python package with __init__.py

app = create_app()

# only if we run this file (not if we just import it) to run the webserver
if __name__ == '__main__':
    app.run(debug=True) # debug = True -> reruns whenever python code is changed