FROM norm/fuzzer-base-image
ARG DEBIAN_FRONTEND=noninteractive
ARG ENV
RUN echo "ENV: $ENV"


# install dependencies
RUN apt update
RUN apt install -y g++ make automake zlib1g-dev libboost-all-dev graphviz graphviz-dev dos2unix
RUN pip3 install py010parser six intervaltree Jinja2 graphviz pygraphviz networkx markdown

# build format fuzzer
RUN git clone https://github.com/uds-se/FormatFuzzer.git
WORKDIR /FormatFuzzer
RUN touch configure Makefile.in
RUN ./configure

# run the converter
WORKDIR /source
ADD source/ .

# Boilerplate code to propergate ENV variables to entrypoint script.
ARG ENV
ARG RQ
ENV ENV=$ENV
ENV RQ=$RQ

# TODO lower permissions, should not be required to run as root
ENTRYPOINT [ "bash", "entrypoint.sh"]
#ENTRYPOINT ["python3", "-m", "BTMeetsCFG" ]