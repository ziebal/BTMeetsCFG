FROM ubuntu:20.04

RUN apt update
RUN apt -y upgrade
RUN apt install -y python3-dev python3-pip git

# Verify python3 was successfully installed and is version 3.8.5
RUN python3 -V

# Offical installation instructions. https://www.fuzzingbook.org/html/Importing.html
RUN pip3 install fuzzingbook