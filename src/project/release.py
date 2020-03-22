from pyh import main
server=main.PhyApp(debug=False)
server.setroot("./template")
app=server.app
if __name__=="__main__":
    server.start()