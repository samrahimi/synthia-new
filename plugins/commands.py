
from plugins.dalle import render, cleanup_urls

def thumbnail(url, size, prompt):
        return f'''
        <a href="{url}"><img src="{url}" width="{size}" alt="{prompt}" /></a>
        '''
def parse(reply, return_as="html"):
    if ("@@DRAW" in reply):
                prompt = reply.split("@@DRAW")[1].split("@@")[0]
                print("debug: got dalle request, will return img thumbnails as HTML when done")
                img_urls = render(prompt)
                print(*img_urls, sep = "\n")

                print("render complete for "+prompt)
    

                if (return_as == "list"):
                        return img_urls
                thumbs = [thumbnail(u, "100%", prompt) for u in img_urls]
                orig = "<!-- results of image prompt " + reply + " -->"
                return orig + "\n".join(thumbs)
    return reply

    print(*cleaned_urls, sep = "\n")
    return cleaned_urls
    print(
        "SYSTEM MESSAGE: image generation has completed, downloading images")
    [download_url(cleaned_url) for cleaned_url in image_urls]
    reply = chatgpt.chat(user_name="SYSTEM MESSAGE", query="the command has completed and the images have been saved to the current working directory")
    print(reply)
