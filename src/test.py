from pyh import main
import uvicorn
app=main.app
main.get_pyh("/","./template/test.phy")
if __name__=="__main__":
    uvicorn.run(app,host="127.0.0.1",port=1234)