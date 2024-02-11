FROM ubuntu

RUN apt-get update

# git 
RUN apt install sudo
RUN sudo apt-get install -y git
RUN git clone https://github.com/ogwayk/valorant_bot.git

# vim
RUN sudo apt-get install -y vim

# python
RUN sudo apt-get install -y python3 python3-pip

#package
RUN pip install git+https://github.com/floxay/python-riot-auth.git
COPY requirements.txt .
RUN pip install -r requirements.txt