import os
import openai
import credentials
openai.api_key =credentials.secrets.get("openai_key")
from plugins.download import download_files

#usage as a library:
#import render from dalle
#render(see below for function arguments)
def render(prompt="a giant hamster with a bitcoin in his mouth", n=4, size="1024x1024"):
  #print(prompt, n, size)
  resp = openai.Image.create(
    prompt=prompt,
    n=n,
    size=size
  )
  urls = [result["url"] for result in resp.data]
  return download_files(urls)
  return urls

# Python code to remove the querystring from a list of urls 
# If a url does not have a querystring it is left unchanged 
def cleanup_urls(url_list):
    clean_url_list = []
    for url in url_list:
        if '?' in url:
            clean_url = url.split('?')[0]
            clean_url_list.append(clean_url)
        else:
            clean_url_list.append(url)
    return clean_url_list

#usage as a command line tool
#python3 dalle.py --prompt "hello world" --n 1 --size "1024x1024"
if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("--prompt")
  parser.add_argument("--n")
  parser.add_argument("--size")

  args = parser.parse_args()

  prompt=args.prompt if args.prompt is not None else "A giant hamster eating a bitcoin sandwich"
  n=int(args.n) if args.n is not None else 1
  size=args.size if args.size is not None else "1024x1024"
  print("Rendering "+prompt)
  response = render(prompt=prompt, n=n, size=size)
  #print(response)
  print("Done. Saved files")
