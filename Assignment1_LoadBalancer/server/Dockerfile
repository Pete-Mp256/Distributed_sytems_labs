# Use a lightweight Python image
FROM python:3.11-slim

# Prevent Python from buffering output
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py .

# Expose application port
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]