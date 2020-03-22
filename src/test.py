from pyh import main
import uvicorn
phyServer=main.PhyApp()
phyServer.setroot("./template")
if __name__=="__main__":
    phyServer.start(host="127.0.0.1",port=1234)