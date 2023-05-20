import base64 

# 把png图标转换成py文件
# 实现在pyinstaller打包时把图标打包

with open('App.png', 'rb') as f:
    b = base64.b64encode(f.read())

with open('icon.py', 'w', encoding='utf-8') as f:
    f.write("img = %s" % b)