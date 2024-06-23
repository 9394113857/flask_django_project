# Use an official Python runtime as the base image
FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file to the working directory
COPY requirements.txt /code/

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask project code to the working directory
COPY . /code/

# Expose the port that the Flask application will run on
EXPOSE 5000

# Set the command to run the Flask application
CMD python app.py
