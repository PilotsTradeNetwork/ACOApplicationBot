# To build a new docker image

$ docker build -t yourname/acobot:latest .

# To run in a container

Make a local dir to store your .env and database files

$ mkdir /opt/acobot
$ cp .env /opt/acobot
$ cp .ptnuserdata.json /opt/acobot
$ mkdir /opt/acobot/dumps

Run the container:

$ docker run -d --restart unless-stopped --name acobot -v /opt/acobot:/root/acobot yourname/acobot:latest
