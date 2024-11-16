# Use an official Python 3.4 image
FROM python:3.4

# Set the working directory
WORKDIR /app

# # Install any additional dependencies
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libssl-dev \
#     zlib1g-dev

COPY requirements.txt .

RUN python -m ensurepip && \
    python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

# Set default command
CMD ["python"]