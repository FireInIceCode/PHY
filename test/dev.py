import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.system("uvicorn release:app --reload")