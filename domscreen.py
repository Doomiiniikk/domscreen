#!/usr/bin/env python
import pathlib
import subprocess
import re
import sys
import time
import json

# TODO Logging system
# TODO Answer questions
# TODO Create README.MD
# TODO Better mainloop i.e. interactive()
# TODO Decide on TUI or console program


class dom_screen():
    
    def __init__(
        self,
        server_name = "server"
        ) -> None:

        self.homeDir : pathlib.Path = pathlib.Path.home()
        self.configDir : pathlib.Path = self.homeDir.joinpath(".config/domscreen")
        self.savedServers : pathlib.Path = self.configDir.joinpath("savedServers.json")
        self.server_name = server_name
        
        if not self.homeDir.is_dir(): raise FileExistsError("This home does not exists") #? Is this proper?
        if not self.configDir.is_dir(): self.configDir.mkdir()
        if not self.savedServers.is_file(): self.m_jWrite(self.savedServers, dict({}))
        
        self.serverDir = self.m_validateServerName(server_name).get("path")
        if not self.serverDir:
            self.m_addTosavedServers(serverName=self.server_name)
            
        try:
            self.config : dict = self.m_jRead(self.savedServers)
        except json.JSONDecodeError:
            self.m_addTosavedServers()
        
        self.server_arguments : None
        # print(self.server_dir)

        if not self.m_validateScreenInstall():
            print("Screen is not installed on your system")
            exit(1)
            
    #!## END OF INIT ##!#
    
    def m_jRead(self, file : pathlib.Path) -> dict:
        """Reads from a configuration file"""
        if not file.is_file(): raise FileExistsError("Path does not point to a file.")
        
        try:
            return json.loads(
                file.read_text()
            )
            #with open(file, "r") as f:
            #    return json.load(fp=f)
        except json.JSONDecodeError as e:
            return dict({})
            # raise json.JSONDecodeError("The requested file does not contain a valid JSON structure.", e.doc, e.pos )

        except PermissionError:
            raise PermissionError("domscreen does not have access to the desired file.")
        
    def m_jWrite(self, file: pathlib.Path, structure : dict, force : bool = False) -> None:
        """Writes to a configuration file"""
        
        if not file.is_file(): raise FileExistsError("Path does not point to a file.")
        if not force and not isinstance(structure, dict): raise TypeError("The given configuration is not a dict and cannot be saved.")
        if not force and not structure: raise ValueError("Empty configuration cannot be saved.")
        
        
        
        try:
            file.write_text(
                json.dumps(
                    structure,
                    indent=4,
                    sort_keys=True
                )
            )
         #   with open(file, "w") as f:
        #        json.dump(structure, f, indent=4)

        except json.JSONDecodeError as e: raise json.JSONDecodeError(
            "The requested file does not contain a valid JSON structure.", e.doc, e.pos )
        except PermissionError: raise PermissionError(
            "domscreen does not have access to the desired file.")
        
    def m_jAppend(self, file : pathlib.Path, structure : dict) -> None:
        """Appends a configuration file"""
        #?#? okay to let exceptions pass because they're implemented in jRead and jWrite?
        
        readStructure : dict = self.m_jRead(file)
        structure = {**structure, **readStructure}
        
        self.m_jWrite(
            file,
            structure
        )
    
    def m_clearFile(self, file : pathlib.Path) -> bool:
        """Wrapper for jWrite but with an empty dictionary"""
        if self.m_jWrite(
            file, dict({}),
            force=True
        ): return True
        
        return False
    
    def m_validateServerName(self, name : str) -> dict | None:
        """Validates if the server name is saved"""
        return self.m_checksavedServers().get(name)
    
    def m_checksavedServers(self) -> dict:
        try:
            return self.m_jRead(self.savedServers)
        except json.JSONDecodeError:
            print("No servers have been saved")
            return dict({}) #?#?# Okay to return an empty dict? It shouldn't be used by the program
    
    def m_prettyCheckSavedServers(self) -> str:
        return json.dumps(
            self.m_checksavedServers(),
            indent=4
        )
    
    def m_addTosavedServers(self,
        serverName = None,
        serverPath = None,
        serverFile = None
        ) -> None:
        
        
        if not serverName:
            for x in range(0, 3):
                serverName : str = input("What do you want to call this server? ")
                if not serverName in self.m_jRead(self.savedServers).keys():
                    break
                
                print("This servername is already taken")
            else:
                print("Couldn't get a name that isn't used, exiting.")
                return None
            
        if not serverPath:
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
        if not serverFile:
            for x in range(0, 3):
                serverFile : pathlib.Path = serverPath.joinpath(
                    input("what's the server file name? ")
                )
                
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
        
        self.m_jAppend(self.savedServers, structure)
        print(f"Added {serverName} to savedServers.json")

    def m_deleteFromsavedServers(self, name: str = None) -> None:
        if not name:
            name = input("No name was given, please enter a valid name.")
        savedServersDict = self.m_checksavedServers()
        if not savedServersDict.get(name):
            print(f"{name} is not in savedServers.json")
            return None
        savedServersDict.pop(name)
        
        self.m_jWrite(self.savedServers, savedServersDict)
        print(f"Removed {name} from savedServers.json")
            
    def m_changeServer(self, name : str = "") -> None:
        if not name:
            name = input(f"Name was not given, please input one. ")
            
        if not self.m_validateServerName(name):
            print("That server is not saved")
            return None
        self.server_name = name
        print(f"Selected {name}")
    
    def summon(self):
        if self.query_sessions() == True:
            print(f"{self.server_name} is already used in another session")
            return
        subprocess.run(f"screen -S {self.server_name} -d -m java -Xmx4G -jar server.jar", shell=True, cwd=self.serverDir)
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
              \rattach : attaches to a screen session
              \rlist : lists all saved servers
              \radd : Saves a server
              \rdel : Deletes a saved server
              \rswitch: switches server
        """)
            


def interactive(ds : dom_screen):
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
                case "clean":
                    cleanScreen()
                case "add":
                    ds.m_addTosavedServers()
                case "list":
                    print(ds.m_prettyCheckSavedServers())
                case "del":
                    ds.m_deleteFromsavedServers()
                case "switch":
                    ds.m_changeServer()
                case _:
                    ds.c_help()
        except EOFError:
            sys.stdin = open(
                "/dev/stdin"
            )
        except KeyboardInterrupt:
            if input(
                "\nDid you want to exit? "
                ) not in [
                    "n", "no", "non"
                ]:
                
                break

def cleanScreen():
    print("\x1b[1;1f\x1b[2J")

if __name__ == "__main__":

    ds = dom_screen(server_name="finsnickarna")

    print("\x1b[?1049h")
    cleanScreen()
        
    arguments : list = sys.argv[1:]
    
    if "-interactive" in arguments:
        interactive(ds)
    else:
        interactive(ds)
    
    # ended program
    
    print("\x1b[?1049l\x1b[1A")        
    
    if "-cleanscreen" in arguments:
        cleanScreen()
        
