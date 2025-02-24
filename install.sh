#!/usr/bin/env bash

function check_code() {
    set -x; 

    if $1;
    then
        echo Success: $2
    else
        echo ERROR: Failed $2 1>&2
        exit 1
    fi

    set +x;
}

read NS3_VERSION < network/ns3_version

echo -e "\n\n Updating enviroment... \n" 

sudo apt-get update && sudo apt-get -y -q upgrade
sudo apt-get -y -q dist-upgrade

echo -e "\n\n Installing required packages ... \n" 
sudo apt-get update

check_code "sudo apt-get install -y -q net-tools gnupg gnupg2 wget curl ca-certificates lsb-release software-properties-common apt-transport-https g++ python3 python3-dev python3-setuptools pkg-config cmake ninja-build git python3-pip python-is-python3 autoconf cvs bzr unzip p7zip-full libc6-dev libclang-dev llvm-dev automake libffi-dev" "Installing required packages"


echo -e "\n\n Installing Ns3 required packages ... \n" 
# from https://www.nsnam.org/wiki/Installation

check_code "sudo apt-get -y -q install ccache" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q gdb valgrind clang-format clang-tidy uncrustify" "Installing Ns3 required packages"

# sudo PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install --user cppyy 2> /dev/null

check_code "sudo apt-get -y -q install cmake-format"

check_code "sudo apt-get install -y -q qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q openmpi-bin openmpi-common openmpi-doc libopenmpi-dev" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q mercurial" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q doxygen graphviz imagemagick" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q texlive texlive-extra-utils texlive-latex-extra texlive-font-utils dvipng latexmk" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q python3-sphinx dia" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q libeigen3-dev" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q gsl-bin libgsl-dev libgslcblas0" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q tcpdump" "Installing Ns3 required packages"

sudo apt-get install -y -q sqlite 2> /dev/null

check_code "sudo apt-get install -y -q sqlite3 libsqlite3-dev" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q libgtk-3-dev" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q vtun lxc uml-utilities ebtables bridge-utils" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q libxml2 libxml2-dev libboost-all-dev" "Installing Ns3 required packages"

check_code "sudo apt-get install -y -q gir1.2-goocanvas-2.0 python3-gi python3-gi-cairo python3-pygraphviz gir1.2-gtk-3.0 ipython3" "Installing Ns3 required packages"

echo -e "\n\n Setting ns3 workspace ... \n" 

# cd network/ && git clone https://gitlab.com/nsnam/ns-3-dev.git
# cd ns-3-dev && ./ns3 clean
# ./ns3 configure -d optimized --enable-sudo --disable-examples --disable-tests --disable-python
# ./ns3

cd network/

check_code "wget https://www.nsnam.org/releases/ns-allinone-${NS3_VERSION}.tar.bz2" "Download NS3"

tar xjf ns-allinone-${NS3_VERSION}.tar.bz2 && rm ns-allinone-${NS3_VERSION}.tar.bz2

sudo chmod -R +x  *

echo -e "\n\n compiling NS3 in optimized mode  ... \n"

cd ns-allinone-${NS3_VERSION}

check_code "./build.py --build-options= -- --enable-sudo --disable-examples --disable-tests --disable-python --build-profile=optimized" "Compile NS3"

echo -e "\n\n Testing NS3 ... \n"

cp ns-${NS3_VERSION}/examples/tutorial/first.cc ns-${NS3_VERSION}/scratch/

check_code "./ns-${NS3_VERSION}/ns3" "Compile NS3 test code"

check_code "./ns-${NS3_VERSION}/ns3 run first" "Run NS3 test code"

rm ns-${NS3_VERSION}/scratch/first.cc

cd ../..

echo -e "\n\n Installing Docker required packages  ... \n"

sudo apt-get remove containerd.io -y 2> /dev/null

check_code "sudo apt-get install -y -q docker.io" "Installing Docker"

check_code "sudo docker run hello-world" "Testing Docker"

sudo groupadd docker 2> /dev/null

sudo gpasswd -a $USER docker && sudo usermod -aG docker $USER

/usr/bin/newgrp docker <<EONG

sudo service docker restart

echo -e "\n\n  Verifying  Docker  ... \n"
docker run hello-world

EONG

echo -e "\n\n Installing Network Bridges  ... \n"

check_code "sudo apt-get install -y -q bridge-utils " "Installing Network Bridges"

check_code "sudo apt-get install -y -q uml-utilities" "Installing Network Bridges"

echo -e "\n\n Enabling IPv6 Functionality for Docker  ... \n"

echo -e "Creating /etc/docker/daemon.json ... \n"

sudo touch /etc/docker/daemon.json

printf '%s\n  %s\n  %s\n  %s\n%s' '{' '"ipv6": true,' '"fixed-cidr-v6": "2001:db8:1::/64",' '"experimental": true' '}' | sudo tee /etc/docker/daemon.json >> /dev/null

echo -e "\n\n Enabling buildx Functionality for Docker  ... \n"

check_code "sudo apt-get install -y qemu-user-static" "Installing Required Tools"

sudo apt-get install -y -q binfmt-support 2> /dev/null

check_code "qemu-x86_64-static --version" "Testing Support for Different Architectures"

echo -e "\n\n Installing Docker buildx  ... \n"

sudo apt-get install docker-buildx -y -q 2> /dev/null

# /usr/bin/newgrp docker <<EONG

# sudo service docker restart

# DOCKER_BUILDKIT=1 docker build --platform=local -o . "https://github.com/docker/buildx.git"  1> /dev/null 2>& 1

# EONG

# mkdir -p ~/.docker/cli-plugins
# mv buildx ~/.docker/cli-plugins/docker-buildx
# sudo chmod a+x ~/.docker/cli-plugins/docker-buildx

sudo service docker restart 2> /dev/null

check_code "sudo docker buildx ls" "Checking Docker Buildx"

echo -e "\n\n Everything is installed successfully  ... \n"

GREEN='\033[0;32m'
echo -e "\n\n  ${GREEN}Please reboot now  ... \n"