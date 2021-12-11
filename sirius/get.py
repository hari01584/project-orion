import os
import platform
import requests
import sys
import shutil

machine = platform.uname()
syst = machine[0].lower()
arch = machine[4].lower()

### CONFIGS
ENDPOINT_GIT = "https://api.github.com/repos/fatedier/frp/releases"
MATCH_TAGS = ['v0.38.0', ]
MATCH_TAGS.append(syst)
MATCH_TAGS.append(arch)
### CONFIGS

print("Starting with match tags: ", MATCH_TAGS)
print("API Endpoint: ", ENDPOINT_GIT)

print("Downloading API Data...")
resp = requests.get(url=ENDPOINT_GIT)
data = resp.json()
print("Parsing API Data...")

assets_url = []
for release in data:
    for asset in release['assets']:
        assets_url.append(asset['browser_download_url'])

multiplexed_url = assets_url[0]
max_match = 0
for item in assets_url:
    match = 0
    for tag in MATCH_TAGS:
        if tag in item:
            match += 1
    if(match > max_match):
        multiplexed_url = item
        max_match = match
        
print("Matched %s with %d tags..."%(multiplexed_url, max_match))

print("Starting asset download")
def download(url, filename):
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')

fname = multiplexed_url.rsplit('/', 1)[1]
download(multiplexed_url, fname)
print("Downloaded, now extracting ", fname)
shutil.unpack_archive(fname)
os.remove(fname)

print("Done!! Creating configurations...")

import configparser
config = configparser.ConfigParser()
config['Common'] = {}
config['Common']['dir'] = fname.rsplit('.', 1)[0]
config['Jumble'] = {}
config['Jumble']['Key1'] = 'Val1'
config['Jumble']['Key2'] = 'Val2'
config['Jumble']['Key3'] = 'Val3'

with open('config.ini', 'w') as configfile:
  config.write(configfile)


print("You are all set, please run getconfig.py to download cloud based configurations!!")
