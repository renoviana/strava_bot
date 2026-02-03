FROM assistant-base-python:latest
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt