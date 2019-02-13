FROM python:3.7-alpine

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /app
WORKDIR /app

COPY . .
CMD [ "python", "./app.py" ]

EXPOSE 5000