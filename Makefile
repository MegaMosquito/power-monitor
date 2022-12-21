# My RV power monitor. See README.md for details

DOCKERHUB_ID:=ibmosquito
NAME:="power-monitor"
VERSION:="1.0.0"

#SERIAL_DEVICE:=/dev/tty0
SERIAL_DEVICE:=/dev/ttyUSB0

default: build run

build:
	docker build -t $(DOCKERHUB_ID)/$(NAME):$(VERSION) .

dev: stop build
	docker run -it -v `pwd`:/outside \
          --name ${NAME} \
          --device /dev/mem:/dev/mem \
          --device /dev/gpiomem:/dev/gpiomem \
          --device /dev/spidev0.0:/dev/spidev0.0 \
          --device ${SERIAL_DEVICE}:${SERIAL_DEVICE} \
          $(DOCKERHUB_ID)/$(NAME):$(VERSION) /bin/bash

run: stop
	docker run -d \
          --name ${NAME} \
          --restart unless-stopped \
          --device /dev/mem:/dev/mem \
          --device /dev/gpiomem:/dev/gpiomem \
          --device /dev/spidev0.0:/dev/spidev0.0 \
          --device ${SERIAL_DEVICE}:${SERIAL_DEVICE} \
          $(DOCKERHUB_ID)/$(NAME):$(VERSION)

test:
	echo "Use VLC to test this container."

push:
	docker push $(DOCKERHUB_ID)/$(NAME):$(VERSION) 

stop:
	@docker rm -f ${NAME} >/dev/null 2>&1 || :

clean:
	@docker rmi -f $(DOCKERHUB_ID)/$(NAME):$(VERSION) >/dev/null 2>&1 || :

.PHONY: build dev run push test stop clean

