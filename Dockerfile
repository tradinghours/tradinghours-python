# Use an official Ubuntu base image
FROM ubuntu:latest

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install development dependencies
RUN pip3 install -e ".[dev]"

CMD ["/bin/bash"]

