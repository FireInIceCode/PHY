import os
import re
import sys
import time
from io import BytesIO

import fastapi
import pretty_errors
import uvicorn
from starlette.requests import Request
from starlette.responses import (FileResponse, JSONResponse, Response,
                                 StreamingResponse)

from . import functions, mediatype
from .config import config
import hashlib

indent_re = re.compile("^\s*")

sessions={}

class PhyApp:
    def __init__(self, debug=True):
        self.app = fastapi.FastAPI()
        self.phy = self.dev_phy if debug else self.rel_phy
        self._session_id=0

    def start(self, host="127.0.0.1", port=80):
        uvicorn.run(self.app, host=host, port=port)

    def setroot(self,rootpath):
        rootpath=os.path.join(sys.path[0],rootpath).replace("\\","/")
        def helper(dirpath,webpath="/"):
            path=os.path.join(rootpath,dirpath)
            for item in os.listdir(path):
                itempath=os.path.join(path,item)
                if os.path.isdir(itempath):
                    helper(itempath,webpath+item+"/")
                elif itempath[-3:]=="phy":
                    print(f"Find phy file at {itempath},webpath is {webpath+item}")
                    self.phy(webpath+item,itempath)
                else:
                    print(f"Find static file at {itempath},webpath is {webpath+item}")
                    self.static(webpath+item,itempath)

        helper("./")

    def scan_py(self, phy_text):
        pos = []
        pys = []
        while config["PYTHONLABELSTART"] in phy_text:
            start = phy_text.find(config["PYTHONLABELSTART"])
            end = phy_text.find(config["PYTHONLABELEND"])
            py_text = phy_text[start+len(config["PYTHONLABELSTART"]):end].strip("\n")
            py_text_lns = py_text.split("\n")
            default_indent = indent_re.match(py_text_lns[0]).span()[1]
            for index, ln in enumerate(py_text_lns):
                py_text_lns[index] = ln[default_indent:]
            py_text = "\n".join(py_text_lns)
            
            while config["HTMLLABELSTART"] in py_text:
                label_start=py_text.find(config["HTMLLABELSTART"])
                label_end=py_text.find(config["HTMLLABELEND"])
                label_text=py_text[label_start+len(config["HTMLLABELSTART"]):label_end].strip("\n")
                py_text=py_text[:label_start]+f"echo('''{label_text}''')"+py_text[label_end+len(config["HTMLLABELEND"]):]
                
            phy_text = phy_text[:start]+"$"+phy_text[end+len(config["PYTHONLABELEND"]):]
            pys.append(py_text)
            pos.append((start, end+len(config["PYTHONLABELEND"])))
        return phy_text, pys, pos

    def get_session_id(self):
        self._session_id+=1
        return hashlib.md5(str(self._session_id).encode("utf-8")).hexdigest()

    def run_py(self, phy_text, filepath, request, pos, pys):
        html_text = phy_text
        session_id=request.cookies.get(config["SESSIONIDNAME"])
        locals_dict={}
        globals_dict = {
            '__file__': filepath,
            '__cookies__': request.cookies,
            '__params__': request.query_params,
            '__url__': request.url,
            '__headers__': request.headers,
            '__method__': request.method,
            '__request__': request,
            '__session__':sessions.get(session_id)[0] if sessions.get(session_id,(0,0))[1]>time.time() else {}
        }
        for key in functions.namespace:
            globals_dict[key] = functions.namespace[key]

        df = 0

        response=None

        for (start, end), py_text in zip(pos, pys):
            output = ""

            def echo(*args, seq=" ", end=""):
                nonlocal output
                if type(output)!=str:
                    raise ValueError("Output not is str,maybe you have being echo a file")
                args = list(args)
                for index, arg in enumerate(args):
                    args[index] = str(arg)
                output += (seq.join(args)+end).replace("\n", "<br>\n")    

            def echofile(filepath_or_data,filetype=None):
                nonlocal output
                if type(filepath_or_data)==str:
                    basedir=os.path.dirname(filepath)
                    with open(os.path.join(basedir,filepath_or_data),"rb") as f:
                        data=f.read()
                    if not filetype:
                        filetype=filepath_or_data.split(".")[-1]
                else:
                    data=filepath_or_data
                buffer=BytesIO(data)
                response=StreamingResponse(buffer,media_type=mediatype.mediatypetable.get(filetype,"applition/octrem-stream"))

            def exec_func():
                try:
                    exec(py_text, globals_dict, locals_dict)
                except Exception as e:
                    print(f"\nError at {filepath}:\n")
                    print(py_text)
                    print(str(type(e))[8:-2],":",e,"\n")
                    nonlocal output
                    response=Response("500 Server Error",status_code=500,media_type="text/html")
            
            globals_dict["echo"] = echo
            globals_dict["echofile"]=echofile

            exec_func()
            if not response:
                html_text = html_text[:start+df]+output+html_text[start+df+1:]
                df += len(output)-1
            else:
                session_id=session_id or self.get_session_id()
                response.set_cookie(config["SESSIONIDNAME"],session_id,max_age=config["SESSIONMAXAGE"])
                if globals_dict.get("__session__"):
                    sessions[session_id]=(globals_dict["__session__"],time.time()+(config["SESSIONMAXAGE"]))
                else:
                    del sessions[session_id]
                for cookie in globals_dict["__cookies__"]:
                    response.set_cookie(cookie,globals_dict["cookies"][cookie])
                return response
        response=Response(html_text, status_code=200, media_type="text/html")
        session_id=session_id or self.get_session_id()
        response.set_cookie(config["SESSIONIDNAME"],session_id,max_age=config["SESSIONMAXAGE"])
        if globals_dict.get("__session__") is not None:
            sessions[session_id]=(globals_dict["__session__"],time.time()+(config["SESSIONMAXAGE"]))
        elif sessions.get(session_id):
            del sessions[session_id]
        for cookie in globals_dict["__cookies__"]:
            response.set_cookie(cookie,globals_dict["cookies"][cookie])
        return response

    def rel_phy(self, webpath, filepath, methods=("get", "post", "put", "delete")):
        file_path = os.path.join(sys.path[0], filepath)
        with open(file_path, encoding="utf-8") as file:
            phy_text = file.read()

        phy_text, pys, poses = self.scan_py(phy_text)

        async def func(request: Request):
            return self.run_py(phy_text, filepath, request, poses, pys)
        for method in methods:
            getattr(self.app, method)(webpath)(func)

    def dev_phy(self, webpath, filepath, methods=("get", "post", "put", "delete")):
        async def func(request: Request):
            file_path = os.path.join(sys.path[0], filepath)
            with open(file_path, encoding="utf-8") as file:
                phy_text = file.read()

            phy_text, pys, poses = self.scan_py(phy_text)
            return self.run_py(phy_text, filepath, request, poses, pys)
        for method in methods:
            getattr(self.app, method)(webpath)(func)

    def static(self,webpath,filepath):
        async def func():
            return FileResponse(filepath)
        self.app.get(webpath)(func)
