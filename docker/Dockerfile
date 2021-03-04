FROM continuumio/miniconda3

WORKDIR /app
COPY . .
RUN apt-get update 
# Needed for installing tulipy
RUN apt-get install -y python3-dev gcc libc-dev
#RUN ./configure.sh
RUN conda install -v -y requests deprecated pandas gxx_linux-64 scipy bs4
RUN pip3 install websockets==8.1
RUN pip3 install tulipy==0.4.0
RUN pip3 uninstall -y numpy && pip3 install numpy==1.20.1

CMD ["python3", "tbot.py"]
