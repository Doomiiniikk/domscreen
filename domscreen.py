#!/usr/bin/env python
import pathlib
import subprocess
import re
import sys
import time
import json

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

        self.homeDir : pathlib.Path = pathlib.Path.home()
        self.configDir : pathlib.Path = self.homeDir.joinpath(".config/domscreen")
        self.savedServers : pathlib.Path = self.configDir.joinpath("savedServers.json")

        if not self.homeDir.is_dir(): raise FileExistsError("This home does not exists")
        if not self.configDir.is_dir(): self.configDir.mkdir()
        if not self.savedServers.is_file(): self.savedServers.write_text("")
        
        
        if not self.m_checksavedServers():
            self.m_addTosavedServers()
            
        try:
            self.config : dict = self.m_jRead(self.savedServers)
        except json.JSONDecodeError:
            self.m_addTosavedServers()
        
        self.server_dir = server_dir
        self.server_name = server_name
        self.server_arguments : None
        # print(self.server_dir)

        if not self.m_validateScreenInstall():
            print("Screen is not installed on your system")
            exit(1)
    ### END OF INIT ###
    
    def m_jRead(self, file : pathlib.Path) -> dict:
        """Reads from a configuration file"""
        if not file.is_file(): raise FileExistsError("Path does not point to a file.")
        
        try:
            with open(file, "r") as f:
                return json.load(fp=f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError("The requested file does not contain a valid JSON structure.", e.doc, e.pos )

        except PermissionError:
            raise PermissionError("domscreen does not have access to the desired file.")
        
    def m_jWrite(self, file: pathlib.Path, structure : dict, force : bool = False) -> None:
        """Writes to a configuration file"""
        
        if not file.is_file(): raise FileExistsError("Path does not point to a file.")
        if not force and not isinstance(structure, dict): raise TypeError("The given configuration is not a dict and cannot be saved.")
        if not force and not structure: raise ValueError("Empty configuration cannot be saved.")
        
        try:
            with open(file, "w") as f:
                json.dump(structure, f, indent=4)

        except json.JSONDecodeError as e: raise json.JSONDecodeError(
            "The requested file does not contain a valid JSON structure.", e.doc, e.pos )
        except PermissionError: raise PermissionError(
            "domscreen does not have access to the desired file.")
        
    def m_jAppend(self, file : pathlib.Path, structure : dict) -> None:
        """Appends a configuration file"""
        #?#? okay to let exceptions pass because they're implemented in jRead and jWrite?
        
        readStructure : dict = self.m_jRead(file)
        structure = {**structure, **readStructure}
        
        self.m_jWrite(file, structure)
        
    def m_checksavedServers(self) -> dict:
        try:
            return self.m_jRead(self.savedServers)
        except json.JSONDecodeError:
            print("No servers have been saved")
            return dict({}) #?#?# Okay to return an empty dict? It shouldn't be used by the program
    
    def m_addTosavedServers(self, structure : dict | None = None) -> None:
        if not structure:
            for x in range(0, 3):
                serverName : str = input("What do you want to call this server? ")
                if not serverName in self.m_jRead(self.savedServers).keys():
                    break
                
                print("This servername is already taken")
            else:
                print("Couldn't get a name that isn't used, exiting.")
                return None
                
                    
            for x in range(0, 3):
                serverPath : pathlib.Path = pathlib.Path(
                    input(
                        "What's the path to the server directory? ")
                ).resolve()
                
                if serverPath.is_dir(): 
                    break
                print("please try again!")
            else:
                print("This directory does not exist, exiting")
                return None
            for x in range(0, 3):
                serverFile : pathlib.Path = pathlib.Path(input("what's the server file name? "))
                
                if serverFile.is_file():
                    break
                print("please try again!")        
            else:
                print("This file does not exist, exiting")
                return None
        
            structure = dict({f"{serverName}" :
                {"path" : f"{serverPath}",
                    "command" : f"screen -S {serverName} -d -m java -Xmx4G -jar {serverFile}"}
                })
        
        self.m_jWrite(self.savedServers, structure)
    
    def m_clearFile(self, file : pathlib.Path) -> bool:
        """Wrapper for jWrite but with an empty dictionary"""
        if self.m_jWrite(file, dict({}), force=True): return True
        return False
    
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
            if input("\nDid you want to exit? ") not in ["n", "no", "non"]:
                break
            

if __name__ == "__main__":

    ds = dom_screen(server_name="finsnickarna")
    ds.m_addTosavedServers()

    exit(0)
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
        
