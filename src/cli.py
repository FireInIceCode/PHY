import cli_cmd,os
params=cli_cmd.parse()
out=cli_cmd.out
'''
createproject
'''
if params.get("cmd")=="createproject":
    if params.get("name"):
        thispath=os.path.dirname(__file__)
        out("正在创建文件夹...")
        os.mkdir(params.get("name"))
        out("创建成功!",'green','black')
        out("正在复制文件...")
        os.system(f'xcopy /e /s "{thispath}/project" "{os.getcwd()}/{params.get("name")}" ')
        out("复制成功!",'green','black')
    else:
        out("缺少参数name,请使用phycli createproject --name=项目名称创建","red","black")
elif params.get("cmd")=='-h':
    out("使用phycli createproject --name=项目名称以创建项目")
cli_cmd.reset()
        
        
        