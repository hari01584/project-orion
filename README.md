# Project Orion

Connecting localhost of different workstations using [fast-reverse-proxy](https://github.com/fatedier/frp)! (IPv6 Stack)


## Applications
1. Projecting and playing your favourite lan game over internet (like Hamachi!).
2. Exposing local webserver/deployment for testing and showcasing your work.
3. Making IPv4 only application use IPv6 only network to make end-to-end client-client connections.
4. Many more..
## Tech/Principle
![Alt text](https://raw.githubusercontent.com/hari01584/project-orion/main/screenshots/projorion.svg?sanitize=true)

*Schematic of the process involved, notice how everything is done through frpc, henceforth it can be said that project orion is just a configuration manager to run fast-reverse-proxy in very limited but user friendly way.*

APIs (expose, connect) are used with neccesary arguments to expose and connect two workstations in a way that brings the services to their localhost *127.0.0.1*, Project-Orion just simplifies this process of managing different aspects and writing configuration files on your own.

# Project Orion

Connecting localhost of different workstations using fast-reverse-proxy! (IPv6 Stack)


## Installation
Needs Python3+ for running scripts.
1. clone this repository, install requirements and *cd to /sirius*
```
python -m pip install -r requirements.txt
```
2. run *get.py* to download neccesary files for running this project.
```
python get.py
```
3. run *cli.py* to see for all options!
```
python cli.py
```


## Used By

Honestly speaking, project-orion was made to support these projects, this was not supposed to be a *standalone* kind of stuff!
- TIntranet (for EACCESS) - [here](https://github.com/hari01584/xTIntranet)
- TLocalJitsi (link soon)


## Related
Uses fast-reverse-proxy made by @fatedier, link of project is [here](https://github.com/fatedier/frp)
