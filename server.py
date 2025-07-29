from flask import Flask, request, redirect, url_for, jsonify
from datetime import datetime

app = Flask(__name__)
detections = []

@app.route('/')
def reroute():
    return redirect(url_for('motion'))

@app.route('/motion', methods=['POST', 'GET'])
def motion():
    if request.method == 'POST':
        data = request.json
        print(f"[{datetime.now()}]  Motion DETECTED from Node {data['node_id']} at {data['timestamp']}")
        detections.append(data)
        return {'status': 'received'}, 200
    else:
        return jsonify(detections), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
