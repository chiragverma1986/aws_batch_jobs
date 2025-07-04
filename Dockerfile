# Use Oracle Linux 8 as the base image
FROM oraclelinux:8


# Install Oracle Instant Client and Python 3.9
RUN dnf -y update && \
    dnf -y install oracle-release-el8 && \
    dnf -y install oracle-instantclient19.10-basic oracle-instantclient19.10-devel oracle-instantclient19.10-sqlplus && \
    dnf -y module disable python36 && \
    dnf -y module enable python39 && \
    dnf -y install python39 python39-pip python39-setuptools python39-wheel && \
    dnf -y install git && \
    rm -rf /var/cache/dnf

WORKDIR /opt

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY app.py app.py
COPY trigger.sh trigger.sh
