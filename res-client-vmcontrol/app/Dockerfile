# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

#RUN apt-get update && apt-get install -y procps && apt-get install -y iputils-ping &&  apt-get install -y netcat-traditional && apt-get install -y net-tools && rm -rf /var/lib/apt/lists/*

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

ARG NAMESERVER_IP
ARG NAMESERVER_PORT
ARG RESUSERNAME
ARG RESPASSWORD

ENV ENAMESERVER_IP=$NAMESERVER_IP
ENV ENAMESERVER_PORT=$NAMESERVER_PORT
ENV EUSERNAME=$RESUSERNAME
ENV EPASSWORD=$RESPASSWORD

# Run app.py when the container launches
ENTRYPOINT [ "python", "app.py"]