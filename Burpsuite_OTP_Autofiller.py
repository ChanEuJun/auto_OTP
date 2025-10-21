from flask import Flask, request, jsonify
from threading import Lock
import time

# This in-memory store will hold the latest OTP.
# In a real-world, more robust tool, you might use a more sophisticated store.
otp_storage = {
    "otp": None,
    "timestamp": None
}
lock = Lock()

# OTPs are usually short-lived. We'll consider an OTP stale after 120 seconds.
OTP_VALIDITY_SECONDS = 120

app = Flask(__name__)

@app.route('/store_otp', methods=['POST'])
def store_otp():
    """
    Endpoint for the Android app to send the OTP to.
    Expects a JSON payload like: {"otp": "123456"}
    """
    data = request.get_json()
    if not data or 'otp' not in data:
        return jsonify({"status": "error", "message": "Missing 'otp' in payload"}), 400

    received_otp = data['otp']
    with lock:
        otp_storage['otp'] = received_otp
        otp_storage['timestamp'] = time.time()
    
    print(f"[*] Received OTP: {received_otp}")
    return jsonify({"status": "success", "message": f"OTP {received_otp} stored."})

@app.route('/get_otp', methods=['GET'])
def get_otp():
    """
    Endpoint for the Burp Suite extension to fetch the latest OTP.
    It will return the OTP and then clear it to prevent reuse.
    """
    with lock:
        current_time = time.time()
        otp = otp_storage['otp']
        ts = otp_storage['timestamp']

        # Check if the OTP is valid and not stale
        if otp and ts and (current_time - ts) < OTP_VALIDITY_SECONDS:
            # OTP is valid, return it and then clear it
            otp_to_return = otp
            otp_storage['otp'] = None
            otp_storage['timestamp'] = None
            print(f"[*] Fetched and cleared OTP: {otp_to_return}")
            return jsonify({"status": "success", "otp": otp_to_return})
        else:
            # No valid OTP found
            if otp:
                print(f"[*] Stale OTP found and cleared.")
                otp_storage['otp'] = None
                otp_storage['timestamp'] = None
            return jsonify({"status": "error", "message": "No valid OTP available"})

if __name__ == '__main__':
    # Run the server on localhost, accessible from your local network.
    # Ensure your phone and computer are on the same Wi-Fi network.
    # Use '0.0.0.0' to make it accessible from other devices on the network.
    app.run(host='0.0.0.0', port=8088)
