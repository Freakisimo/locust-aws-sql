# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install AWS CLI
RUN apt-get update && \
    apt-get install -y awscli

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files into the container at /app
COPY . .
