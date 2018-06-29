import os
import datetime
import zipfile
import settings
import subprocess
import time
import random
import asyncio
from pymongo import MongoClient

languages = {'python': ['py', '', 'python3 MyBot.py'],
 'java': ['java', 'javac MyBot.java', 'java MyBot'],
 'rust': ['rs', 'cargo rustc --release -q -- -Awarnings', 'target/release/MyBot'],
 'javascript': ['js', '', 'node MyBot.js'],
 'c++': ['cpp', 'set -e && cmake . && make MyBot', './MyBot'],
 'dart': ['dart', '', 'dart MyBot.dart'],
 'go': ['go', 'export GOPATH=$(pwd) && go build MyBot.go', './MyBot'],
 'haskell': ['hs', 'ghc --make MyBot.hs -O -v0 -rtsopts -outputdir dist', './MyBot.exe'],
 'ruby': ['rb', '', 'ruby MyBot.rb'],
 'c#': ['cs', 'xbuild Halite2/Halite2.csproj', 'mono Halite2/bin/Debug/Halite2.exe']}

def log(string):

    """
    A simple log function
    """

    string = "Timestamp: - "+getTime()+" "+ string
    with open(settings.path+"/"+settings.logFile, 'a') as (out):
        out.write(string + '\n')
    return '**' + string + '**'

def getTime():

    """
    Function to get and format current time, just to
    speed things up
    """

    return ('{:%Y-%m-%d %H:%M:%S}').format(datetime.datetime.utcnow())

def str_to_bool(s):

    """
    Helper function to handle json settings
    """

    if s == 'True':
        return True
    if s == 'False':
        return False

def checkPulse():
    return settings.db.arena.find_one({}).get('running')

def manageHandler(start=True):
    if start:
        handler = subprocess.Popen("python3 "+settings.path+"/handler.py", shell=True)
        settings.db.arena.update_one({}, {"$set":{"running":True}}, upsert=True)
    else:
        settings.db.arena.update_one({}, {"$set":{"running":False}}, upsert=True)


async def uploadBot(link, username, fileName):

    """
    Function that downloads zip file, unzips it,
    recognize the language used, stores it into the
    player in the database and then runs the
    compiler function
    """

    username = username.replace(' ', '')
    player = settings.db.players.find_one({"username":username})
    save = settings.path + '/../bots/' + username + '/'

    if player is None:
        player = {
            "username":username,
            "path":save,
            "lang":"",
            "commands":[],
            "flagged":False,
            "running":False
        }
        playerId = settings.db.players.insert_one(player).inserted_id

    else:
        playerId = player.get("_id")

    if not player.get('running'):
        try:
            os.system("rm -r "+save+" > /dev/null 2>&1") #clean up folders
            os.mkdir(save) #create folder
            if fileName[-4:] == '.zip': #check file is a zip file
                os.system('wget -q -O ' + save + fileName + ' ' + link)
                z = zipfile.ZipFile(save + fileName, 'r')
                z.extractall(save)
                z.close()

                found = False
                lang, lib = None, None
                for f in os.listdir(save):
                    if f.startswith('MyBot.'):
                        for k, v in languages.items():
                            if f.replace('MyBot.', '') == v[0]:
                                found = True
                                lang = v
                                if f.replace('MyBot.', '') == "py" and os.path.isfile(save+"requirements.txt"):
                                    lib = os.popen("cd "+save+" && sudo -H pip3 install -r "+save+"requirements.txt").read()

                                elif f.replace('MyBot', '') == "js" and os.path.isfile(save+"package.json"):
                                    lib = os.popen("cd "+save+" && npm install").read()
                                break


                    elif f.startswith("src"):
                        for s in os.listdir(save+"src/"):
                            if s == "MyBot.go":
                                lang = languages.get("go")
                                found = True
                                lib = os.popen("cd "+save+" && go get").read()
                                break
                            elif s == "main.rs":
                                lang = languages.get("rs")
                                found = True
                                break

                    elif f.startswith("Halite2"):
                        for s in os.listdir(save+"Halite2/"):
                            if s == "Halite2.csproj":
                                lang = languages.get("c#")
                                found = True
                                break

                    if found:
                        break

                compileLog = ""
                if lang != None and found:
                    settings.db.players.update_one({"_id":playerId}, {"$set":{"lang":lang[0], "commands":[lang[1], lang[2]]}}, upsert=True)
                    player = settings.db.players.find_one({"_id":playerId})
                    text, compileLog = await compileBot(player)
                    if compileLog != "" :
                        text = "File bot : "+fileName+", "+text

                    if lib != None :
                        text += "\nHere is output of external libraries installation :\n"+lib

                elif lang != None and not found:
                    text = 'File bot : ' + fileName + ' conatins a bot file but the language : '+ext+' isn\'t supported!'

                elif lang == None:
                    text = 'File bot : ' + fileName + ' does not contain a **MyBot** file of any type!'

                log(text)
                return text, compileLog, save + fileName

            return "File wasn't a .zip file, check the rules!", ""

        except Exception as e:
            s = log(str(e))
            return s, "", ""

    else:
        return "Cannot compile "+fileName+", user is already running a battle/match or compiling other code!", ""


async def compileBot(player):

    """
    Function that starts the compiler.
    player = player object from the database
    Function gets all the info needed to compile
    the code of this player from the object and
    adds it to the queue, then waits for it to
    be done ( or returns a timeout error ).
    It returns the result of the compiler and the
    compiler log.
    """

    #clean up logs
    os.system("rm -r "+settings.path+"/../env/out/"+player["username"]+".txt"" > /dev/null 2>&1")
    compileLog = ""
    data = {
        "type":"compile",
        "players":player,
        "status":"not-running",
        "logfile":"",
        "success":False
    }
    queueId = settings.db.queues.insert_one(data).inserted_id
    settings.db.players.update_one({"_id":player.get("_id")}, {"$set":{"running":True}}, upsert=True)

    secs = 0
    text = "took too much time to compile! Max is "+str(240)+"s"
    while secs <= 240:
        q = settings.db.queues.find_one({"_id":queueId})
        if q.get("status") == "finished":
            if q.get("success"):
                compileLog = q.get("logfile")
                if compileLog != "":
                    text = "submitted, compiled and run successfully! Sending log file..."
                else:
                    text = "submitted, compiled and run successfully! Error loading log file..."

            else:
                compileLog = q.get("logfile")
                if compileLog != "":
                    text = "submitted but encountered an error compiling/running! Sending log file..."
                else:
                    text = "submitted but encountered an error compiling/running! Error loading log file as well..."

            break

        else:
            await asyncio.sleep(1)
            secs += 1

    settings.db.queues.delete_one({"_id":queueId})
    settings.db.players.update_one({"_id":player.get("_id")}, {"$set":{"running":False}}, upsert=True)

    return text, compileLog

async def battle(players, width, height, mode, seed=None):

    """
    Function that takes in these parametes:
    players = usernames of the players (array of string)
    width = width of the map for battle (string)
    height = height for the map for battle (string)
    mode = type of battle, (int)
            mode = 0, 1v1 normal battle
            mode = 1, 1v1 match battle
            mode = 2, 2v2 normal battle
            mode = 3, 2v2 match battle
            mode = 4, 4FFA normal battle
            mode = 5, 4FFA match battle
    Function creates a queue in the db, the handler
    stars the battle and here it keeps checking until
    is finished ( or return a timout error ).
    then returns the result of battle, the replay file,
    the player individual logs
    """

    pp = []
    for i in players:
        p = settings.db.players.find_one({"username":i.replace(' ', '')})
        pp.append(p)

    modes = [2, 2, 4, 4, 4, 4]
    types = ["battle", "match", "2v2", "2v2-match", "FFA", "FFA-match"]

    logs = []
    result = ""
    replay = ""
    status = ""

    if len(pp) == modes[mode] and not None in pp:
        battleName = ""
        ready = False
        count = 0
        for p in pp:
            if p.get("running"):
                status = "**Error setting up the battle!** "+p.get("username")+" **is already running something!**"
                ready = False
                break
            battleName += p.get("username")
            if len(pp) == 2:
                battleName += "VS" if count == 0 else ""
            else:
                battleName += "-" if p != pp[-1] else ""
            count += 1
            ready = True

        if ready:
            os.system("rm "+settings.path+"/../env/out/"+battleName+"* > /dev/null 2>&1")

            data = {
                "type":types[mode],
                "players":pp,
                "status":"not-running",
                "logfile":"",
                "success":False,
                "map":[width, height],
                "name":battleName,
                "seed": seed if seed != None else ""
            }
            queueId = settings.db.queues.insert_one(data).inserted_id
            for p in pp:
                settings.db.players.update_one({"_id":p.get("_id")}, {"$set":{"running":True}}, upsert=True)

            secs = 0
            timeout = settings.g.get("timeout") * settings.g.get("max_turns") + settings.g.get("extra_time")
            status = "**Battle took too much time! Max is "+str(timeout)+"s**"

            while secs <= timeout: #time same as env/handler.py
                q = settings.db.queues.find_one({"_id":queueId})
                if q.get("status") == "finished" and os.path.isfile(q.get("logfile")):
                    if mode == 0 or mode == 2 or mode == 4:
                        if os.path.isfile(settings.path+"/../env/out/"+battleName+".hlt"):
                            replay = settings.path+"/../env/out/"+battleName+".hlt"

                            with open(q.get("logfile"), "r") as l:
                                result = "```"+l.read()+"```"

                            for p in pp:
                                found = False
                                for f in os.listdir(p.get("path")):
                                    if f.endswith(".log"):
                                        logs.append(p.get("path")+f)
                                        found = True
                                        break

                                if not found:
                                    logs.append("")


                            status = "**Battle ran successfully, here is the replay and halite output. Sending log files of players in DM...**"

                        else:
                            status = "**Error while running the battle, here is the halite output.**"
                            with open(q.get("logfile"), "r") as l:
                                result = "```"+l.read()+"```"

                    elif mode == 1 or mode == 3 or mode == 5:
                        with open(q.get("logfile"), "r") as l:
                            result = "```"+l.read()+"```"
                        if os.path.exists(settings.path+"/../env/out/"+battleName+"/"+str(int(settings.g.get("runs")))+".hlt"):
                            replay = settings.path+"/../env/out/"+battleName+"/match.zip"
                            status = "**Match ran successfully, here are the results and the replays.**"
                        else:
                            status = "**Error while running the match, here is the halite output.**"

                    break

                else:
                    await asyncio.sleep(1)
                    secs += 1

            settings.db.queues.delete_one({"_id":queueId})
            for p in pp:
                settings.db.players.update_one({"_id":p.get("_id")}, {"$set":{"running":False}}, upsert=True)

    else:
        wrong = ""
        for i in range(len(pp)):
            if pp[i] == None:
                wrong += players[i] + " "
        status = "**Error setting up the battle! "+wrong+"didn't submit!**"

    return status, result, logs, replay
