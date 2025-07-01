FROM ubuntu:24.04
RUN apt-get update; apt-get install -y \
    python3 \
    python3-pip \
    r-base \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    curl \
    git

WORKDIR /app

# R Packages
COPY install_r_packages.R /tmp/install_r_packages.R
RUN Rscript /tmp/install_r_packages.R

COPY . .

RUN pip3 install -r requirements.txt --break-system-packages

CMD ["python3", "main.py"]

