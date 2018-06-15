import os
import threading
import time
import sys
import subprocess
import random
import zipfile
import datetime
import urllib.parse
from pymongo import MongoClient

#these will be hardcoded until we have
#a function to set everything up automatically
username = urllib.parse.quote_plus('arena')
password = urllib.parse.quote_plus(')O2BK%bm1v}*A?U5rYndr=mik>9QBLq^Sb|5^vork{KxE4(A')
mongo = MongoClient('mongodb://%s:%s@localhost:27017/halite-tournaments' % (username, password))

db = mongo["halite-tournaments"]
s = db.arena.find_one({})
game = db.game.find_one({})

path = os.path.dirname(os.path.realpath(__file__))

def log(string):

    """
    Log function
    """

    string = "Timestamp: - {:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())+" "+ string
    with open(path+s.get('log'), 'a') as (out):
        out.write(string + '\n')
    return '**' + string + '**'

def randmizeMap(m):

    """
    Randomize the maps for battle
    """

    if len(m) == 0 or len(m) == 2:
        return game.find("maps")["small"][random.randint(0, 2)]
    elif len(m) == 1 or len(m) == 3:
        return game.find("maps")["big"][random.randint(0, 2)]
    else:
        return game.find("default")

def randomizeSeed():

    """
    Randomize the seed for battle
    """

    return str(random.randint(game["seeds"][0], game["seeds"][1]))

def forrest(): #reference alert

    """
    Check runFile to see if we should run Handler
    """

    return s.get('running')

class BobTheBuilder(threading.Thread): #reference alert

    """
    This Thread takes in the object from the queue,
    finds the compiler and run information about
    the player that submitted the code.
    First it compiles the code, and if that's
    executed properly it runs a game of halite
    against the player's bot to test if
    everything works properly.
    Then it saves the output of the compiler and halite
    into /env/out/
    """

    def __init__(self, q):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.q = q
        self.player = self.q.get('players')
        self.path = self.player.get('path')
        self.log = ""

    def run(self):
        os.system("rm "+self.path+"*.log "+self.path+"*.hlt > /dev/null 2>&1")

        self.comp = self.player.get('commands')[0]
        self.fire = self.player.get('commands')[1]

        if self.comp != "":
            self.log += "*****COMPILER LOG*****\n"
            try:
                output = subprocess.check_output("cd "+self.path+" && "+self.comp, timeout=120, shell=True).decode()
                self.log += output+"\n\n"

            except subprocess.TimeoutExpired:
                self.log += "Timeout Error!\n"

            except subprocess.CalledProcessError as e:
                self.log += str(e)
                self.log += output+"\n\n"

        self.fire = "cd "+self.path+" && "+self.fire
        command = "/."+path+game.get('halite')+" -d \"240 160\" \""+self.fire+"\" \""+self.fire+"\" -i "+path+s.get('out')
        self.log += "*****HALITE LOG*****\n"
        success = False

        try:
            output = subprocess.check_output(command, timeout=120, shell=True).decode()
            self.log += output

            if output.splitlines(True)[-3].startswith("Opening"):
                replay = output.splitlines(True)[-3].split()[4]
                success = True
                os.system("rm "+replay+" > /dev/null 2>&1")
            else:
                status = "failed"

        except subprocess.TimeoutExpired:
            self.log += "Timeout Error!\n"

        except subprocess.CalledProcessError as e:
            self.log += str(e)

        with open(path+s.get('out')+self.name+".txt", "w") as l :
            l.write(self.log)

        db.queues.update_one({"_id":self.q.get("_id")}, {"$set": {"status":"finished", "success":success, "logfile":path+s.get('out')+self.name+".txt"}}, upsert=True)

        self.stop()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

class Arena(threading.Thread):

    """
    This Thread takes in the object from the queue,
    retrieves the players in the battle/match from
    the database, then it runs the halite command
    and saves the replay and the output into the
    env/out/ folder
    """

    def __init__(self, q):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.q = q
        self.players = []
        for p in self.q.get("players"):
            self.players.append(p)
        self.name = self.q.get('name')
        self.type = self.q.get("type")
        if self.type == "match":
            self.maps = []
        else:
            self.sizes = q.get("map")

        self.official = ["match", "2v2-match", "FFA-match"]
        self.log = ""
        self.results = []
        self.out = path+s.get('out')
        self.logFile = ""

    def start(self):
        for p in self.players:
            os.system("rm "+p.get("path")+"*.log  > /dev/null 2>&1")

        success = False

        if self.type in self.official:
            try:
                os.mkdir(self.out)
            except:
                pass
            self.logFile = self.out+"/battle.log"
            self.out += self.name
            zipped = zipfile.ZipFile(self.out+"/match.zip", mode="w")

            for b in range(game.get('runs')):
                self.sizes = randmizeMap(self.maps)
                self.maps.append(self.sizes)
                self.command =  ["/."+path+game.get('halite'), "-d", self.sizes[0]+" "+self.sizes[1]]
                for p in self.players:
                    self.command.append("cd "+p.get("path")+" && "+p.get("commands")[1])
                self.command += ["-i", self.out+"/", "-s", randomizeSeed()]
                if self.type == "2v2-match":
                    self.command.append("--team")

                try:
                    timeout = game.get("timeout") * game.get("max_turns") + game.get("extra_time")
                    o = subprocess.check_output(self.command, timeout=timeout).decode()
                    output = o.splitlines(True)

                    if output[-3].startswith("Opening"):
                        replay = output[-3].split()[4]
                        os.rename(replay, self.out+"/"+str(b+1)+".hlt")
                        tmp = []
                        for i in range(len(self.players)):
                            tmp.append(output[-(i+1)])
                        self.results.append(tmp)
                        zipped.write(self.out+"/"+str(b+1)+".hlt", arcname=str(b+1)+".hlt")
                        success = True
                    else :
                        self.log += "ERROR RUNNING BATTLE:\n\n"+output

                except subprocess.TimeoutExpired:
                    self.log += "Timeout Error\n"

                except Exception as e:
                    self.log += str(e)+"\n"

            zipped.close()

        else:
            self.logFile = self.out+self.name+".log"
            self.command =  ["/."+path+game.get('halite'), "-d", self.sizes[0]+" "+self.sizes[1]]
            for p in self.players:
                self.command.append("cd "+p.get("path")+" && "+p.get("commands")[1])
            self.command += ["-i", self.out, "-s", randomizeSeed()]
            if self.type == "2v2":
                self.command.append("--team")

            try:
                timeout = game.get("timeout") * game.get("max_turns") + game.get("extra_time")
                o = subprocess.check_output(self.command, timeout=timeout).decode()
                output = o.splitlines(True)
                checker = -(len(self.players)+1) if self.type != "2v2" else -3

                if output[checker].startswith("Opening"):
                    replay = output[checker].split()[4]
                    os.rename(replay, self.out+self.name+".hlt")
                    tmp = []
                    w = len(self.players) if self.type != "2v2" else 2
                    for i in range(w):
                        tmp.append(output[-(i+1)])
                    self.results.append(tmp)
                    success = True
                else :
                    self.log += "ERROR RUNNING BATTLE:\n\n"+o

            except subprocess.TimeoutExpired:
                self.log += "Timeout Error\n"

            except Exception as e:
                self.log += str(e)+"\n"
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.log += "Encountered exception : "+str(e)+"\n\t"+str(exc_type)+" -- "+str(fname)+" -- "+str(exc_tb.tb_lineno)

        num = 1
        for r in self.results:
            self.log += "Round number : "+str(num)+"\n\n"
            for p in r:
                self.log += p+"\n"
            self.log += "\n\n"
            num += 1

        with open(self.logFile, "w") as l:
            l.write(self.log)

        db.queues.update_one({"_id":self.q.get("_id")}, {"$set": {"status":"finished", "success":success, "logfile":self.logFile}})

        self.stop()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class Handler(threading.Thread):

    """
    This Thread scans through the queue
    and if it finds something in queue that
    is "not-running" it starts up either
    Arena, for battles, or BobTheBuilder for compiler
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.max = s.get('max')
        self.queue = []

    def start(self):
        while forrest():
            self.space = self.max
            for q in db.queues.find({"type":"compile"}):
                if self.space == 0:
                    break
                if q.get('status') == "not-running":
                    thread = BobTheBuilder(q)
                    thread.setName(q.get('players').get('username'))
                    self.queue.append(thread)
                    self.space -= 1
                    db.queues.update_one({"_id":q.get('_id')}, {"$set":{"status":"running"}}, upsert=True)
                    thread.start()
                else:
                    continue

            if self.space > 0:
                queues = [db.queues.find({"type":"match"}),
                        db.queues.find({"type":"2v2-match"}),
                        db.queues.find({"type":"FFA-match"}),
                        db.queues.find({"type":"battle"}),
                        db.queues.find({"type":"2v2"}),
                        db.queues.find({"type":"FFA"})]

                for b in queues:
                    for q in b:
                        if self.space == 0:
                            break
                        if q.get('status') == "not-running":
                            thread = Arena(q)
                            thread.setName(q.get('name'))
                            self.queue.append(thread)
                            self.space -= 1
                            db.queues.update_one({"_id":q.get('_id')}, {"$set":{"status":"running"}}, upsert=True)
                            thread.start()
                        else:
                            continue

            while len(self.queue) > 0:
                for thread in self.queue :
                    if thread.stopped():
                        self.queue.remove(thread)

            time.sleep(1)


    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

if __name__ == '__main__':
    try:
        if forrest(): #if we are running
            h = Handler()
            h.setName("hand")
            print("Starting handler up...")
            h.start()
        else :
            print("Handler is not running... sad.")

    except KeyboardInterrupt:
        pass
