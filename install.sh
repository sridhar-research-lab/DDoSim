#!/usr/bin/env bash

# This script install all the required packages for The NS3DockerEmulator  https://github.com/chepeftw/NS3DockerEmulator 
# To running , open Terminal and execute  
# source install.sh

echo -e "\n\n Updating enviroment... \n" 

sudo apt-get update && sudo apt-get -y -q upgrade
sudo apt-get -y -q dist-upgrade

echo -e "\n\n Installing required packages ... \n" 
sudo apt-get install -y net-tools

echo -e "\n\n Installing Ns3 required packages ... \n" 

sudo apt-get install -y g++ python3 python3-dev pkg-config sqlite3 python3-setuptools qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools cmake ninja-build git libffi7

sudo apt-get install -y gir1.2-goocanvas-2.0 python3-gi python3-gi-cairo python3-pygraphviz gir1.2-gtk-3.0 ipython3 

sudo apt-get install -y openmpi-bin openmpi-common openmpi-doc libopenmpi-dev

sudo apt-get install -y autoconf cvs bzr p7zip-full

sudo apt-get install -y gdb valgrind uncrustify

sudo apt-get install -y doxygen graphviz imagemagick texlive texlive-extra-utils texlive-latex-extra texlive-font-utils dvipng latexmk

sudo apt-get install -y tcpdump sqlite3 libsqlite3-dev libxml2 libxml2-dev libc6-dev libc6-dev-i386 automake python3-pip

python3 -m pip install --user cxxfilt pyyaml ninja

sudo apt-get install libudev1
#sudo mkdir /var/run/uuidd
#sudo chown uuidd:uuidd /var/run/uuidd
#sudo mkdir /run/uuidd
sudo apt-get install uuid-runtime
#sudo chown uuidd:uuidd /run/uuidd

sudo apt-get install -y libgtk-3-dev

sudo apt-get install -y vtun lxc uml-utilities libxml2 libxml2-dev libboost-all-dev

echo -e "\n\n Setting ns3 workspace ... \n" 

cd ns3/ && git clone https://gitlab.com/nsnam/ns-3-dev.git

# cp -fr csma-net-device.cc ns-3-dev/src/csma/model/
# cp -fr csma-net-device.h ns-3-dev/src/csma/model/

echo -e "\n\n compoling NS3 in optimized mode  ... \n"

cd ns-3-dev

./ns3 clean
./ns3 configure -d optimized --enable-sudo --disable-examples --disable-tests --disable-python
./ns3

echo -e "\n\n Running first ns3 example  ... \n"
cp examples/tutorial/first.cc scratch/
./ns3
./ns3 run scratch/first
cd ~

echo -e "\n\n Installing Docker required packages  ... \n"

#service lxcfs stop
#sudo apt-get remove lxc-common lxcfs lxd lxd-client

#Uninstall old versions. Older versions of Docker were called docker, docker.io, or docker-engine. If these are installed, uninstall them:
sudo apt-get remove docker
sudo apt-get remove docker.io
sudo apt-get remove containerd
sudo apt-get remove runc
sudo apt-get remove docker-engine

sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

sudo systemctl enable systemd-resolved.service

if [ $(lsb_release -i | awk '{print $(NF-0);exit}') == "Debian" ]; then
	curl -4fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
	echo \
	  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
	  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
else
	curl -4fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
fi

#sudo systemctl restart systemd-networkd.service
sudo apt-get -o Acquire::ForceIPv4=true update && sudo apt-get -o Acquire::ForceIPv4=true install -y docker-ce docker-ce-cli containerd.io

sudo groupadd docker
sudo gpasswd -a $USER docker
sudo usermod -aG docker $USER

#sudo chmod 666 /var/run/docker.sock
/usr/bin/newgrp docker <<EONG

sudo service docker restart

echo -e "\n\n  Verifying  Docker  ... \n"
docker run hello-world

EONG

echo -e "\n\n Installing Network Bridges  ... \n"

sudo apt-get install -y bridge-utils 
sudo apt-get install -y uml-utilities

echo -e "\n\n Enabling IPv6 Functionality for Docker  ... \n"

echo -e "Creating /etc/docker/daemon.json ... \n"

sudo touch /etc/docker/daemon.json
printf '%s\n  %s\n  %s\n%s' '{' '"ipv6": true,' '"fixed-cidr-v6": "2001:db8:1::/64"' '}' | sudo tee /etc/docker/daemon.json >> /dev/null

sudo service docker restart

echo -e "\n\n Everything is installed successfully  ... \n"

GREEN='\033[0;32m'
echo -e "\n\n  ${GREEN}Please reboot now  ... \n"