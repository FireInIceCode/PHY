import sys,re
from colorama import Fore,Back,Style,init
init(autoreset=True)
def parse():
    params={}
    argv=sys.argv[1:]
    for arg in argv:
        if "=" in arg:
            key,value=arg[2:].split("=")
            params[key]=value
        else:
            params["cmd"]=arg
    return params
def out(text:str,color:str="white",bg:str="black"):
    print(getattr(Fore,color.upper())+getattr(Back,bg.upper())+text)

def reset():
    print(Style.RESET_ALL)
    