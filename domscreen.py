#!/usr/bin/env python
import pathlib
import subprocess
import re
import sys
import time
import signal
# todo
# timer for startup
# counter for kill
# clean input and output
# add config file with loose variable, instead of hard coded server name
# backup system
# Gather the correct directory automatically


class dom_screen():
    
    def __init__(
        self,
        server_dir = pathlib.Path(__file__).parent,
        server_name = "server"
    ) -> None:
    
        self.server_dir = server_dir
        self.server_name = server_name
        self.server_arguments : None
        # print(self.server_dir)
    
        if not self.m_validateScreenInstall():
            print("Screen is not installed on your system")
            exit(1)
        
    
    def summon(self):
        if self.query_sessions() == True:
            print(f"{self.server_name} is already used in another session")
            return
        subprocess.run(f"cd {self.server_dir}", shell=True)
        subprocess.run(f"screen -S {self.server_name} -d -m java -Xmx4G -jar server.jar", shell=True)
        print(f"Created a session with name {self.server_name}")
    
    def attach(self):
        if self.query_sessions() == False:
            print(f"Session with name \"{self.server_name}\" doesn't exist")
            return
        subprocess.run(f"screen -Dr {self.server_name}", shell=True)
        print(f"Attached to session {self.server_name}")
    
    def detach(self):
        if self.query_sessions() == False:
            print(f"Session with name {self.server_name} doesn't exist")
            return
        subprocess.run(f"screen -S {self.server_name} -D", shell=True)
        
    def kill(self):
        if self.query_sessions() == False:
            print(f"Session with name {self.server_name} doesn't exist")
            return
        subprocess.run(f"screen -S {self.server_name} -X stuff stop\r", shell=True)
        print(f"Killed session {self.server_name}")

    def query_sessions(self, index=0):
        sessions = subprocess.run("screen -ls", shell=True, capture_output=True).stdout.decode("utf-8").split("\n")
        sessions = "\n".join( sessions[1:-2] ) + "\r"
        
        reg = "\\s+(\\d+)\\." + self.server_name + "\\s+\\((.+?)\\)\\s+\\((\\w+)\\)"
        if mymatch := re.findall(reg, sessions):
            if index < 0:
                index = 0
            if index > len(mymatch) - 1:
                index = len(mymatch) - 1
            return True
        return False
    
    def m_validateScreenInstall(self):
        if subprocess.run("which screen", shell=True, capture_output=True).stdout.decode("utf-8") == "":
            return False
        return True
            
    
    def c_help(self):
        print("""commands:
              \rbreak : breaks the main loop
              \rstart : Starts a server, if not already started
              \rdetach : detaches a remotely attached screen session. Don't know its usefulness
              \rkill : sends stop command to the session, hopefully shuts the server down
              \rattach : attaches to a screen session""")


def interactive():
    print("Running in interactive mode")
    while 1:
        try:
            get = input()
            match get:
                case "break":
                    break
                case "start":
                    ds.summon()
                case "attach":
                    ds.attach()
                case "kill":
                    ds.kill()
                case "detach":
                    ds.detach()
                case _:
                    ds.c_help()
        except EOFError:
            sys.stdin = open("/dev/stdin")
        except KeyboardInterrupt:
            def toHand(signum, frame):
                raise TimeoutError
            signal.signal(signal.SIGALRM, toHand)
            try:
                while 1:
                    signal.alarm(5)
                    response = input("\nDid you want to exit? ")
                    signal.alarm(0)
                    if response not in ["n", "no", "non"]:
                        break
            except (TimeoutError, KeyboardInterrupt):
                break
            

if __name__ == "__main__":
    
    ds = dom_screen(server_name="finsnickarna")

    print("\x1b[?1049h")
    print("\x1b[1;1f\x1b[2J")
        
    arguments : list = sys.argv[1:]
    
    if "-interactive" in arguments:
        interactive()
    else:
        interactive()
    
    # ended program
    
    print("\x1b[?1049l\x1b[1A")        
    
    if "-cleanscreen" in arguments:
        print("\x1b[1;1f\x1b[2J")
        print("cleaned your screen as asked")
        time.sleep(2)
        print("\x1b[1;1f\x1b[2J")
        
