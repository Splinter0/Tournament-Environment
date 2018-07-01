killall mongod
setsid mongod --dbpath mongo/data --port 27017 --storageEngine wiredTiger --auth &
python3 handler/main.py
