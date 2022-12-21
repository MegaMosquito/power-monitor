FROM debian

# Install the necessary code
RUN apt update && apt install -y python3-pip jq fonts-dejavu python3-pil
RUN pip3 install adafruit-circuitpython-rgb-display RPi.GPIO pyserial

# In the RV, we are mostly in the America/Los_angeles timezone, and these
# hosts have no way to determine their physical location from the Starlink
# internet service that we use almost always. So I am har-coding it here:
RUN echo "tzdata tzdata/Areas select America" | debconf-set-selections
RUN echo "tzdata tzdata/Zones/America select Los_Angeles" | debconf-set-selections
RUN rm -f /etc/localtime /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

# Copy over the source
COPY pm.py /
WORKDIR /

# Run the daemon
CMD python3 pm.py

