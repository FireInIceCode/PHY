import os
os.chdir(os.path.dirname(__file__))
os.system("uvicorn release:app --reload")