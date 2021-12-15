import os
import platform
import requests
import sys
import shutil

machine = platform.uname()
syst = machine[0].lower()
arch = machine[4].lower()
if(arch == 'x86_64'):
    arch = 'amd64' # Correction for git repo

### CONFIGS
ENDPOINT_GIT = "https://api.github.com/repos/fatedier/frp/releases"
MATCH_TAGS = ['v0.38.0']
MATCH_TAGS.append(syst)
MATCH_TAGS.append(arch)
### CONFIGS

print("Starting with match tags: ", MATCH_TAGS)
print("API Endpoint: ", ENDPOINT_GIT)

print("Downloading API Data...")
resp = requests.get(url=ENDPOINT_GIT)
data = resp.json()
print("Parsing API Data...")

if('message' in data):
    print(data['message'])
    exit(0)

assets_url = []
for release in data:
    for asset in release['assets']:
        assets_url.append([asset['browser_download_url'], 0])

for item in assets_url:
    for tag in MATCH_TAGS:
        if tag in item[0]:
            item[1] += 1

assets_url = sorted(assets_url, key=lambda x: x[1], reverse=True)
multiplexed_url = assets_url[0][0]
max_match = assets_url[0][1]

def yes_or_no(question):
    reply = input(question+" (y/n): ").lower().strip()
    if reply[0] == "y":
        return True
    if reply[0] == "n":
        return False
    else:
        return yes_or_no("Uhhhh... please enter ")

def get_choice(n):
    try:
        val = int(input("Choose an option [0-%d]: "%(n-1, )))
        if val < 0 or val > n:
            raise ValueError
        return val
    except ValueError:
        print("Invalid option, Choose again ")
        return get_choice(n)

print("Matched %s with %d tags..."%(multiplexed_url, max_match))
if(max_match != len(MATCH_TAGS)):
    if(yes_or_no("Matching successful but one or more tags are missing, Do you want to select version on your own?")):
        n = 10
        for i in range(n):
            print("[%d] %s"%(i, assets_url[i][0]))
        index = get_choice(n)
        multiplexed_url = assets_url[index][0]
        max_match = assets_url[index][1]

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
                sys.stdout.write('\r[{}{}]'.format('=' * done, '.' * (50-done)))
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
config['Common']['dir'] = fname.replace('.zip','').replace('.tar.gz', '')
config['Common']['name'] = 'frpc.exe' if os.name == 'nt' else 'frpc'
# config['Jumble'] = {}
# config['Jumble']['Key1'] = 'Val1'
# config['Jumble']['Key2'] = 'Val2'
# config['Jumble']['Key3'] = 'Val3'

with open('config.ini', 'w') as configfile:
  config.write(configfile)
