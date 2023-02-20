import uuid
import os
import requests

def download_files(urls):
    for url in urls:
        # Generate a unique file name
        file_name = uuid.uuid4().hex + '.png'
        # Fetch the file from the URL
        response = requests.get(url)
        # Save the file to the current working directory
        with open(os.path.join(os.getcwd(), file_name), 'wb') as f:
            f.write(response.content)