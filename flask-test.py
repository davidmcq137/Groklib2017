from __future__ import print_function
from flask import Flask, redirect, url_for, request
app= Flask(__name__)

@app.route('/', methods=['POST','GET'])
def index():
    return('<html><body><h1>Hello World<h1></body></html>')

@app.route('/act/<name>', methods=['POST', 'GET'])
def act_name(name):
    if request.method=='POST':
        print('POST!')
    else:
        print('GET!')
            
    return 'Hello %s!' %name

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5137)

    
