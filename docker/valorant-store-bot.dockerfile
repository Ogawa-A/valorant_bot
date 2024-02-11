FROM ubuntu

# git 
RUN apt install sudo
RUN sudo apt-get install git
RUN git clone https://github.com/ogwayk/valorant_bot.git

# vim
RUN sudo apt-get install vim

# python
RUN apt-get update
RUN sudo apt-get install -y python3 python3-pip

#package
RUN pip install git+https://github.com/floxay/python-riot-auth.git
RUN pip install -r requirements.txt

