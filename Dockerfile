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

COPY . .

RUN pip3 install -r requirements.txt --break-system-packages

# R Packages
RUN Rscript -e "install.packages(c('fmsb', 'ggplot2'), repos='https://cloud.r-project.org')"

CMD ["python3", "main.py"]

