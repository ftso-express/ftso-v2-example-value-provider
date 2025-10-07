# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY src_py/ ./src_py/

# Make port 3101 available to the world outside this container
EXPOSE 3101

# Define environment variable
ENV VALUE_PROVIDER_CLIENT_PORT=3101

# Run main.py when the container launches
CMD ["python", "src_py/main.py"]