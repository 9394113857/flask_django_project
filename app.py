from flask import Flask, render_template
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/app1/')
def app1_view():
    response = requests.get('http://localhost:8000/app1/')
    return response.content

@app.route('/app1/second/')
def app1_second_view():
    response = requests.get('http://localhost:8000/app1/second/')
    return response.content

@app.route('/app2/')
def app2_view():
    response = requests.get('http://localhost:8000/app2/')
    return response.content

@app.route('/app2/second/')
def app2_second_view():
    response = requests.get('http://localhost:8000/app2/second/')
    return response.content

if __name__ == '__main__':
    app.run(debug=True)
