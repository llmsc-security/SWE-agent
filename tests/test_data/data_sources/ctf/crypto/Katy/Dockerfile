FROM ubuntu:14.04
MAINTAINER unknonwn
LABEL Description="CSAW 2016 LCG" VERSION='1.0'

#installation
RUN dpkg --add-architecture i386
RUN apt-get update && apt-get upgrade -y 
RUN apt-get install -y build-essential socat

#user
RUN adduser --disabled-password --gecos '' katy 
RUN chown -R root:katy /home/katy/
RUN chmod 750 /home/katy

#Copying file
WORKDIR /home/katy/
COPY server /home/katy

#Run the program with socat

# --- Auto-Generated Entrypoint Configuration ---
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN mkdir -p /var/log && touch /var/log/app.log
EXPOSE 4242
ENTRYPOINT ["/entrypoint.sh"]
