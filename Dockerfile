FROM python:3.10-slim-buster
RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot
COPY setup.py .
COPY README.md .
COPY ptn ptn
RUN pip3 install .
RUN mkdir /root/acobot
RUN ln -s /root/acobot/.ptnuserdata.json /root/.ptnuserdata.json
RUN ln -s /root/acobot/.env /root/.env
WORKDIR /root/acobot
ENTRYPOINT ["/usr/local/bin/aco"]
