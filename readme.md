这是一个仿造PHP,可以实现将Python代码嵌入HTML的程序.
最近听说有些人喜欢用PHP,因为它可以直接写到HTML中,可以让开发效率变快,本着人生苦短我选Python的想法,我设计了这个可以将Python嵌入HTML程序,并直接使用web服务器运行的程序.
嵌入后的文件扩展名是phy,支持两种语法:

&lt;py><br>
    python代码
<br>&lt;/py>

其中支持全部的Python语法,包括import.还提供了关于web的一些变量:
- \_\_cookies\_\_:提供请求的cookie
- \_\_file\_\_:当前文件的路径
- \_\_params\_\_:请求中含有的query查询参数
- \_\_url\_\_:请求的url对象,包含path:路径等属性
- \_\_headers\_\_:请求头
- \_\_method\_\_:请求方法
- \_\_request\_\_:请求原始对象,starlette.request.Request的实例
- \_\_session\_\_:会话对象,字典

还有两个内置方法:
- echo(text:str,*args,seq=" ",end=""):使用类似print,返回请求
- echofile:返回一个文件使用,一个参数,可以是相对于当前文件的文件路径,也可以是文件的bytes数据.
- echourl:返回一个重定向请求,一个参数,url

如果需要在py中使用html标签,可以使用<label></label>,在其中包裹html代码段,

<label>html代码</label>=echo("""html代码""")

我的联系方式:
- email(可能不经常看): miaoxingren2006@163.com
- qq(回的比较快):8955859

欢迎大家为此项目贡献代码!
