import requests

# Path to your image
image_path = r"C:\Users\laure\Downloads\Clerodendrum.jpg"

# URL of your running Flask server
url = "http://localhost:5000/analyze-plant"

# Optional message to include with the image
message = "Please identify this plant and assess its health. Pay special attention to the leaf shape, arrangement, and any flowers. This should be a Clerodendrum species - please confirm or correct this identification."

with open(image_path, "rb") as img_file:
    files = {"file": img_file}
    data = {"message": message}
    response = requests.post(url, files=files, data=data)

print("Status code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception:
    print("Response text:", response.text) 