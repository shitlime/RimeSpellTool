import tkinter as tk
import threading
import sys

from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
import tkinter.font as tkFont
from tkinter import END

import SpellTool
from SpellTool import *

class App(tk.Frame):
    """
    拼运调试器 Demo GUI界面
    """
    def __init__(self, master=None):
        """
        界面初始化
        """
        super().__init__(master)
        self.grid()
        self.appName = "RIME Spell Tool/雾凇魔法工具 v0.4"
        self.master.title(self.appName)
        # 字体
        fontfamilylist = tkFont.families()
        if '宋体' in fontfamilylist:
            fontFamily = '宋体'
        else:
            fontFamily = fontfamilylist[0]
        self.font = tkFont.Font(family=fontFamily, size=11)

        # =====浏览方案=====
        # -----标签-----
        self.schemaLable = tk.Label(master, width=20, text='Schema/方案文件：')
        self.schemaLable.grid(row=0, column=0)
        # -----显示路径-----
        self.schemaEntry = tk.Entry(master, width=80)
        self.schemaEntry.grid(row=0, column=1, columnspan=4)
        # -----按钮-----
        self.schemaButton = tk.Button(
            master,
            text='浏览方案',
            command=self.findSchema,
            width=20,
            height=1,
        )
        self.schemaButton.grid(row=0, column=5)

        # =====浏览词库=====
        # -----标签-----
        self.dictLable = tk.Label(master, width=20, text='Dict/词库文件：')
        self.dictLable.grid(row=1, column=0)
        # -----显示路径-----
        self.dictEntry = tk.Entry(master, width=80)
        self.dictEntry.grid(row=1, column=1, columnspan=4)
        # -----按钮-----
        self.dictButton = tk.Button(
            master,
            text='浏览词库',
            command=self.findDict,
            width=20,
            height=1,
        )
        self.dictButton.grid(row=1, column=5)


        # =====表格=====
        self.tree = ttk.Treeview(master)
        # 字体
        style = ttk.Style()
        style.configure("Treeview", font=self.font)
        # 显示行数
        self.tree["height"] = 20
        # -----表头-----
        # 隐藏首列
        self.tree["show"]='headings'
        # 设置列
        self.tree["columns"] = ("序号", "字词", "码", "algebra", "preedit_format")
        self.tree.column("序号", width=50)
        self.tree.column("字词", width=200)
        self.tree.column("码", width=200)
        self.tree.column("algebra", width=200)
        self.tree.column("preedit_format", width=200)
        self.tree.heading("序号", text="序号")
        self.tree.heading("字词", text="字词")
        self.tree.heading("码", text="码")
        self.tree.heading("algebra", text="algebra")
        self.tree.heading("preedit_format", text="preedit_format")
        self.tree.grid(row=2, column=0, columnspan=6)
        # -----绑定滚动条-----
        ybar = ttk.Scrollbar(master, orient='vertical')
        self.tree["yscrollcommand"] = ybar.set
        ybar['command'] = self.tree.yview
        ybar.grid(row=2, column=5, sticky='NSE')
        # -----颜色-----
        self.tree.tag_configure("rowTag", background="#F3F3F3")
        self.tree.tag_configure("derive", foreground="green", background="#ECFFEB")

        # ======操作按钮======
        self.nextAction = tk.Button(
            master,
            text='下一条',
            command=self.nextAction,
            width=10,
            height=2
        )
        self.nextAction.grid(row=3, column=0)

        self.allAction = tk.Button(
            master,
            text='全部执行',
            command=self.allAction,
            width=10,
            height=2
        )
        self.allAction.grid(row=3, column=1)

        self.loadButton = tk.Button(
            master,
            text='加载/重载',
            command=self.loadFiles,
            width=10,
            height=2
        )
        self.loadButton.grid(row=3, column=2)

        self.saveButton = tk.Button(
            master,
            text='保存\n当前表单结果',
            command=self.saveResult,
            width=10,
            height=2
        )
        self.saveButton.grid(row=3, column=3)

        self.saveAllButton = tk.Button(
            master,
            text='转换词库\n并保存',
            command=self.saveAll,
            width=10,
            height=2
        )
        self.saveAllButton.grid(row=3, column=4)

        self.exit = tk.Button(
            master,
            text='退出',
            command=sys.exit,
            width=10,
            height=2
        )
        self.exit.grid(row=3, column=5)

        # ======信息栏======
        self.infoBox = scrolledtext.ScrolledText(master, width=120, height=10)
        self.infoBox.configure(state='disabled')
        self.infoBox.tag_config('stderr', foreground='#b22222')
        self.infoBox.grid(row=4, columnspan=6)
        # 重定向标准输出
        sys.stdout = TextRedirector(self.infoBox, "stdout")
        sys.stderr = TextRedirector(self.infoBox, "stderr")

        print(f"{self.appName}    项目地址：https://github.com/shitlime/RimeSpellTool")
        sys.stderr.write("提示：红色信息表示程序出错信息\n")

        # ======逻辑代码======
        # 拼写工具类
        self.st = SpellTool()

        

    def insertData(self, data: list[list[str]]):
        """
        往表格添加数据
        """
        # 清空以前的行
        for child in self.tree.get_children():
            self.tree.delete(child)
        # 插入新的行
        for index, d in enumerate(data):
            index += 1
            # 行颜色
            tags = []
            if index % 2 == 0:
                tags.append("rowTag")
            if d[0] == '(derive)':
                tags = "derive"
            # 插入语句
            self.tree.insert(
                "",
                index=index,
                values=(
                    index,
                    d[0] if (d[0] != '(derive)') else "",
                    d[1] if (d[1] != '(derive)') else "",
                    d[2] if (len(d) >= 3) and (self.st.algebra) else "(None)",
                    d[3] if (len(d) >= 4) and (self.st.preedit_format) else "(None)"
                ),
                tags=tags
            )

    def findSchema(self):
        """
        浏览方案
        """
        schemaFileName = filedialog.askopenfilename(
            title='选择方案文件',
            filetypes=[('方案文件', '.schema.yaml'), ('所有文件', '*')]
        )
        self.schemaEntry.delete(0, 'end')
        self.schemaEntry.insert(0, schemaFileName)

    def findDict(self):
        """
        浏览词库
        """
        dictFileName = filedialog.askopenfilename(
            title='选择词库文件',
            filetypes=[('词库文件', '.dict.yaml'), ('所有文件', '*')]
        )
        self.dictEntry.delete(0, 'end')
        self.dictEntry.insert(0, dictFileName)
    
    def nextAction(self):
        """
        下一条
        """
        # 判断是否已经加载数据
        if not('actionFlag' in vars(self).keys()):
            messagebox.showinfo("提示", "请先加载/重载")
            return
        # 执行一条
        if self.actionFlag == 0:
            # algebra部分
            if next(self.algebra, False):
                self.insertData(self.st.dict)
                return
            else:
                self.actionFlag += 1
                messagebox.showinfo("提示", "algebra部分已经执行完毕！接下来开始执行preedit_format部分")
                return
        elif self.actionFlag == 1:
            # preedit_format部分
            if next(self.preeditFormat, False):
                self.insertData(self.st.dict)
                return
            else:
                self.actionFlag += 1
                messagebox.showinfo("提示", "preedit_format部分已经执行完毕！")
                return
        # 全部执行完后
        else:
            messagebox.showinfo("提示", "已经全部执行完毕！若要重新开始请点击“加载/重载”")
        

    def loadFiles(self):
        """
        装载文件
        """
        print("装载文件中。。。")
        # 读数据
        schemaPath = self.schemaEntry.get()
        dictPath = self.dictEntry.get()
        if schemaPath == '' or dictPath == '':
            messagebox.showinfo("提示", "未选择方案和词库文件！")
            print("未选择方案和词库文件！")
            return
        self.st.readSchemaFile(schemaPath)
        self.st.readDictFile(dictPath, 2000)
        # algebraAction迭代器
        self.algebra = self.st.algebraAction()
        # preedit_format迭代器
        self.preeditFormat = self.st.preeditFormatAction()
        # 设置执行状态标记
        self.actionFlag = 0
        # 在表格中显示
        self.insertData(self.st.dict)
        print("装载完成！")
    
    def allAction(self):
        """
        执行全部
        """
        def fun():
            # algebra
            while next(self.algebra, False):
                pass
                # self.insertData(self.st.dict)
            else:
                self.actionFlag += 1
            # preeditFormat
            while next(self.preeditFormat, False):
                pass
                # self.insertData(self.st.dict)
            else:
                self.actionFlag += 1
                self.insertData(self.st.dict)
                print("全部执行完成。")

        # 判断是否已经加载数据
        if not('actionFlag' in vars(self).keys()):
            messagebox.showinfo("提示", "请先加载/重载")
            return
        # 执行全部-新线程
        # t = threading.Thread(target=fun)
        # t.start()
        fun()

    def saveResult(self):
        # 判断是否已经加载数据
        if not('actionFlag' in vars(self).keys()):
            messagebox.showinfo("提示", "请先加载/重载")
            return
        savePath = filedialog.asksaveasfilename(title='保存结果')
        if savePath:
            with open(savePath, "w", encoding='utf-8') as f:
                f.write('\n'.join([ '\t'.join(l) for l in self.st.dict ]))
            print(f"已经保存：{savePath}")
    
    def saveAll(self):
        """
        转换并整个词库文件，并保存结果
        """
        def fun():
            # 1.读数据
            schemaPath = self.schemaEntry.get()
            dictPath = self.dictEntry.get()
            if schemaPath == '' or dictPath == '':
                messagebox.showinfo("提示", "未选择方案和词库文件！")
                print("未选择方案和词库文件！")
                return
            if not messagebox.askyesno("转换词库并保存",
                                "是否开始转换？"
                                +"\n请注意："
                                +"\n1.将在信息栏输出转换信息"
                                +"\n2.转换过程中，你仍然可以继续进行调试"
                                +"\n3.转换过程中，会占用较多系统资源，可能会感到卡顿"
                                +"\n4.转换完成后，会有弹窗提醒"):
                return
            st = SpellTool()
            st.readSchemaFile(schemaPath)
            st.readDictFile(dictPath)
            # 2.执行全部
            # algebraAction迭代器
            algebra = st.algebraAction()
            # preedit_format迭代器
            preeditFormat = st.preeditFormatAction()
            while next(algebra, False):
                pass
            while next(preeditFormat, False):
                pass
            # 3.保存
            print("整个词库转换完成！请选择保存路径。")
            messagebox.showinfo("转换词库并保存", "全部转换完成！请选择保存路径。")
            savePath = filedialog.asksaveasfilename(title='保存转换结果')
            if savePath:
                with open(savePath, "w", encoding='utf-8') as f:
                    f.write('\n'.join([ '\t'.join(l) for l in st.dict ]))
                print(f"已经保存：{savePath}")
            else:
                print("未选择保存路径，视为放弃保存。")
        t = threading.Thread(target=fun)
        t.start()

class TextRedirector(object):
    """
    文本重定向器

    将打印输出的文本重定向
    """

    def __init__(self, widget: scrolledtext.ScrolledText , tag='stdout'):
        """
        创建一个文本重定向器
        """
        self.widget = widget
        self.tag = tag
    
    def write(self, str):
        """
        重定向器的输出
        """
        self.widget.configure(state='normal')
        self.widget.insert(END, str, (self.tag, ))
        self.widget.configure(state='disable')
        # 移动到最下方
        self.widget.see(END)



if __name__ == "__main__":
    app = App()
    # app.master.maxsize(860, 680)
    # 窗口大小不可变
    # app.master.resizable(0, 0)
    # 启动
    app.mainloop()