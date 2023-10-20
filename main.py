from flask import Flask , jsonify , request
from gpt import main;

app = Flask(__name__)

@app.route('/query')
def hello_world():
    data = request.get_json()
    print(data)
    return jsonify(main(data["query"]))
    

if __name__ == '__main__':
    app.run(debug=True)