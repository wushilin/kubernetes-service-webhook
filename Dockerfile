# Use a minimal Python image
FROM python:3.13

# Set the working directory
WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the webhook script
COPY flask-webhook.py .

# Expose port 443 for HTTPS
EXPOSE 443

# Run the Flask application with TLS
CMD ["python", "flask-webhook.py"]
