#update
sudo apt-get update
#install python3, pip3 and mongoDB
sudo apt-get install python3 python3-pip mongodb-org
#install discord API
sudo -H pip3 install discord
#install mongoDB API
sudo -H pip3 install pymongo
#install cmake
sudo apt-get install cmake
#install rust
curl -sf -L https://static.rust-lang.org/rustup.sh | sh
#install java
sudo apt-get install -y default-jre
sudo apt-get install default-jdk
#install ruby
sudo apt-get install -y ruby
#install nodejs
curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
sudo apt-get install -y nodejs
#install python3
sudo apt-get install -y python3-pip
sudo pip3 install tensorflow
sudo pip3 install numpy
#install dart
sudo apt-get install apt-transport-https
sudo sh -c 'curl https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -'
sudo sh -c 'curl https://storage.googleapis.com/download.dartlang.org/linux/debian/dart_stable.list > /etc/apt/sources.list.d/dart_stable.list'
sudo apt-get update
export PATH=/usr/lib/dart/bin:$PATH
sudo sh -c 'curl https://storage.googleapis.com/download.dartlang.org/linux/debian/dart_unstable.list > /etc/apt/sources.list.d/dart_unstable.list'
sudo apt-get install dart
#install golang
wget https://dl.google.com/go/go1.10.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.10.linux-amd64.tar.gz
rm go1.10.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bi
sudo apt-get install gccgo-go
#install c# compiler
sudo apt-get install mono-complete

#setting permissions for arena
#chmod 777 *
#chmod 770 db/ LICENSE README.md imgs/ season-3/ install.sh \
#ht.sh env/Engine/ env/README.md handler/.gitignore handler/arena.sh \
#handler/bot.log handler/funcs.py handler/main.py handler/handler.py \
#handler/README.md handler/settings.py
#chmod 775 env/halite

#setting up iptables for arena
#iptables -A OUTPUT -s 127.0.0.1/32 -m owner --uid-owner 1002 -j ACCEPT
#iptables -A INPUT -s 127.0.0.1/32 -j ACCEPT
#iptables -A OUTPUT -m owner --uid-owner 1002 -j DROP
