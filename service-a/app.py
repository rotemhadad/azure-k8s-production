#service-a/app.py
from flask import Flask, jsonify, render_template_string
import requests
import time
from threading import Thread, Lock

app = Flask(__name__)

current_bitcoin_value = 0
average_bitcoin_value = 0
bitcoin_values = []
lock = Lock()

def get_bitcoin_value():
    try:
        response = requests.get('https://api.coindesk.com/v1/bpi/currentprice/BTC.json')
        response.raise_for_status()
        data = response.json()
        rate = data['bpi']['USD']['rate'].replace(',', '')
        return float(rate)
    except Exception as e:
        print(f"Error fetching Bitcoin value: {e}")
        return None

def update_bitcoin_value():
    global current_bitcoin_value, bitcoin_values, average_bitcoin_value
    while True:
        value = get_bitcoin_value()
        if value is not None:
            with lock:
                current_bitcoin_value = value
                bitcoin_values.append(value)
                if len(bitcoin_values) > 10:
                    bitcoin_values = bitcoin_values[-10:] 
                if (len(bitcoin_values)!=0):    
                    average_bitcoin_value = sum(bitcoin_values) / len(bitcoin_values) if bitcoin_values else 0
        time.sleep(60)



@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
        <head>
            <script>
                function updateValues() {
                    fetch('/service-a/get_values')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.json();
                        })
                        .then(data => {
                            document.getElementById('current_value').textContent = data.current_value.toFixed(2);
                            document.getElementById('average_value').textContent = data.average_value.toFixed(2);
                        })
                        .catch(error => {
                                console.error('Error:', error);
                                });
                }
                function tryConnectToB() {
                    fetch('/service-a/try_connect_to_b')
                        .then(response => response.text())
                        .then(data => {
                            document.getElementById('connection_result').textContent = data;
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            document.getElementById('connection_result').textContent = 'Error: ' + error.message;
                        });
                }

                setInterval(updateValues, 60000);
                updateValues(); 
            </script>
        </head>
        <body>
              <h1>Bitcoin Value (USD)</h1>
            <p>Current Value: $<span id="current_value">Loading...</span></p>
            <p>Average Value (last 10 minutes): $<span id="average_value">Loading...</span></p>
            <button onclick="tryConnectToB()">Try to connect Service B</button>
            <p>Connection result: <span id="connection_result"></span></p>
        </body>
    </html>
    ''')

@app.route('/get_values')
def get_values():
    with lock:
        current_value = current_bitcoin_value
        average_value = average_bitcoin_value
    return jsonify({
        'current_value': current_value,
        'average_value': average_value
    })


@app.route('/try_connect_to_b')
def try_connect_to_b():
    service_b_url = "http://service-b:82"
    try:
        response = requests.get(service_b_url, timeout=5)
        return f"Tried to connect to: {service_b_url}. Status: {response.status_code}, Content: {response.text[:100]}"
    except requests.exceptions.RequestException as e:
        return f"Failed to connect to Service B ({service_b_url}): {str(e)}"


if __name__ == '__main__':
    Thread(target=update_bitcoin_value, daemon=True).start()
    app.run(host='0.0.0.0', port=81, debug=True)


