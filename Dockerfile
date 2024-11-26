# Use the official Python 3.11 image as the base image
FROM python:3.11-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the requirements.txt file from the local machine to the /app directory inside the container
COPY requirements/prod.txt requirements.txt

# Install docker inside the webserver container
RUN curl -sSL https://get.docker.com/ | sh
# Install the Python dependencies listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire local directory into the /app directory inside the container
COPY . .

# Use Gunicorn to run the Flask application
CMD ["python", "main.py"]

