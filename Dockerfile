FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]

# Run the application
# CMD ["gunicorn", "--worker-class", "gevent", "--workers", "2", "--worker-connections", "50", "--bind", "0.0.0.0:5000", "run:app"]
