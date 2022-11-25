FROM debian

# Install the necessary code
RUN apt update && apt install -y python3-pip jq fonts-dejavu python3-pil
RUN pip3 install adafruit-circuitpython-rgb-display RPi.GPIO pyserial

# Copy over the source
COPY pm.py /
WORKDIR /

# Run the daemon
CMD python3 pm.py

