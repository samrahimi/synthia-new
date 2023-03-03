import uuid
import os
import requests
import credentials


def download_files(urls):
    return_urls=[] #the relative paths of the images that we've written to disk, servable by the webapp
    for url in urls:
        # Generate a unique file name
        file_name = uuid.uuid4().hex + '.png'
        # Fetch the file from the URL
        # Download the image from the URL
        import urllib
        from urllib.parse import urlsplit
        response = requests.get(url=urlsplit(url).geturl())
        # Save the file to the current working directory
        with open(os.path.join(os.getcwd()+"/static/img_dalle", file_name), 'wb') as f:
            f.write(response.content)
        
        return_urls.append("/static/img_dalle/"+file_name)
    return return_urls