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


def get_pyh(webpath, filepath):
    @app.get(webpath)
    async def func(request: Request):

        file_path = os.path.join(sys.path[0], filepath)
        with open(file_path, encoding="utf-8") as file:
            pyh_text = file.read()
        while "<py>" in pyh_text:
            start = pyh_text.find("<py>")
            end = pyh_text.find("</py>")
            py_text = pyh_text[start+len("<py>"):end].strip("\n")

            py_text_lns = py_text.split("\n")
            default_indent = indent_re.match(py_text_lns[0]).span()[1]
            for index, ln in enumerate(py_text_lns):
                py_text_lns[index] = ln[default_indent:]
            py_text = "\n".join(py_text_lns)

            output = ""

            def echo(*args,seq=" ",end=""):
                nonlocal output
                args=list(args)
                for index,arg in enumerate(args):
                    args[index]=str(arg)
                output += (seq.join(args)+end).replace("\n","<br>")

            globals_dict = {
                "echo": echo,
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
            def exec_func():
                try:
                    exec(py_text, globals_dict, locals_dict)
                except Exception as e:
                    nonlocal output
                    output = "500 Server Error"
                    print(e)

            exec_func()
            pyh_text = pyh_text[:start]+output+pyh_text[end+len("</py>"):]

        return Response(pyh_text, status_code=200, media_type="text/html")
