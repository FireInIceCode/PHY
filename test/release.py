from pyh import main
server=main.PhyApp(debug=True)
server.setroot("./template")
app=server.app
if __name__=="__main__":
    server.start()