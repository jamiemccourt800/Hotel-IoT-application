FROM mongo:6.0


RUN apt-get update && apt-get install -y python3 python3-pip

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

# Copy your Python script
COPY sample-data.py /docker-entrypoint-initdb.d/sample-data.py
COPY init.sh /docker-entrypoint-initdb.d/init-demo.sh
