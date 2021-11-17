FROM python:3

RUN mkdir -p /opt/app
WORKDIR /opt/app
COPY . /opt/app/

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

ENTRYPOINT ["/opt/app/entrypoint.sh"]
