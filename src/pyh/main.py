import os
import sys
import re

import fastapi
import pretty_errors
from starlette.responses import Response
from starlette.requests import Request

from . import functions

indent_re = re.compile("^\s*")

app = fastapi.FastAPI()


def get_html(el):
    return unescape(html.tostring(el).decode("utf-8"))


def get_inner(el):
    text = get_html(el)
    return text[text.find(">")+1:text.rfind("</")]

def scan_py(pyh_text):
    pos=[]
    pys=[]
    while "<py>" in pyh_text:
        start=pyh_text.find("<py>")
        end=pyh_text.find("</py>")
        py_text = pyh_text[start+len("<py>"):end].strip("\n")
        py_text_lns = py_text.split("\n")
        default_indent = indent_re.match(py_text_lns[0]).span()[1]
        for index, ln in enumerate(py_text_lns):
            py_text_lns[index] = ln[default_indent:]
        py_text = "\n".join(py_text_lns)
        pyh_text=pyh_text[:start]+"$"+pyh_text[end+len("</py>"):]
        pys.append(py_text)
        pos.append((start,end+len("</py>")))
    return pyh_text,pys,pos

def run_py(pyh_text,filepath,request,pos,pys):
    html_text=pyh_text
    globals_dict = {
        "__file__": filepath
    }

    locals_dict = {
        'cookies': request.cookies,
        'params': request.query_params,
        'url': request.url,
        'headers': request.headers,
        'method':request.method,
        'request':request
    }
    for key in functions.namespace:
        locals_dict[key]=functions.namespace[key]

    df=0

    for (start,end),py_text in zip(pos,pys):
        output = ""
        def echo(*args,seq=" ",end=""):
            nonlocal output
            args=list(args)
            for index,arg in enumerate(args):
                args[index]=str(arg)
            output += (seq.join(args)+end).replace("\n","<br>\n")
        def exec_func():
            try:
                exec(py_text, globals_dict, locals_dict)
            except Exception as e:
                nonlocal output
                output = "500 Server Error"
                print(e)
        globals_dict["echo"]=echo
        exec_func()
        html_text = html_text[:start+df]+output+html_text[start+df+1:]
        df+=len(output)-1
    return html_text


def pyh(webpath, filepath,methods=("get","post","put","delete")):

    file_path = os.path.join(sys.path[0], filepath)
    with open(file_path, encoding="utf-8") as file:
        pyh_text = file.read()

    pyh_text,pys,poses=scan_py(pyh_text)
    
    async def func(request: Request):
        html_text=run_py(pyh_text,filepath,request,poses,pys)
        return Response(html_text, status_code=200, media_type="text/html")
    for method in methods:
        getattr(app,method)(webpath)(func)
