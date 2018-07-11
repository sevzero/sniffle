FROM ubuntu:18.04

ENV http_proxy=http://192.168.20.14:3128
ENV https_proxy=http://192.168.20.14:3128

RUN apt-get -y update
RUN apt-get -y install vim wget build-essential flex bison libpcre3-dev libdumbnet-dev zlib1g-dev python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install flask flask-sqlalchemy
RUN mkdir /snort_src 
WORKDIR /snort_src
RUN wget https://www.snort.org/downloads/snort/daq-2.0.6.tar.gz && tar -xvzf daq-2.0.6.tar.gz
WORKDIR daq-2.0.6
RUN apt-get -y install libpcap-dev libpcap0.8 sudo
RUN ./configure && make && sudo make install
WORKDIR /snort_src
RUN wget https://www.snort.org/downloads/snort/snort-2.9.11.1.tar.gz && tar -xvzf snort-2.9.11.1.tar.gz
WORKDIR snort-2.9.11.1
RUN ./configure --enable-sourcefire && make && sudo make install
RUN ldconfig && groupadd snort && useradd snort -r -s /sbin/nologin -c SNORT_IDS -g snort
RUN mkdir -p /etc/snort/rules && \
	mkdir /var/log/snort && \
	mkdir /usr/local/lib/snort_dynamicrules && \
	chmod -R 5775 /etc/snort && \
	chmod -R 5775 /var/log/snort && \
	chmod -R 5775 /usr/local/lib/snort_dynamicrules && \
	chown -R snort:snort /etc/snort && \
	chown -R snort:snort /var/log/snort && \
	chown -R snort:snort /usr/local/lib/snort_dynamicrules && \
	touch /etc/snort/rules/white_list.rules && \
	touch /etc/snort/rules/black_list.rules && \
	touch /etc/snort/rules/local.rules && \
	cp /snort_src/snort-2.9.11.1/etc/*.conf* /etc/snort && \
	cp /snort_src/snort-2.9.11.1/etc/*.map /etc/snort
RUN mkdir -p /data/ && chown snort:snort /data
USER snort
WORKDIR /etc/snort/web
ENTRYPOINT ["python3", "runserver.py"]
