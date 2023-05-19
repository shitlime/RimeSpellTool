import regex
import yaml

class SpellTool(object):
    def __init__(self) -> None:
        pass

    def readDictFile(self, path, limit=0):
        """
        读取字典文件

        path: 字典文件路径
        limit: 读取数量限制
        """
        dictionary = None
        with open(path, 'r', encoding='utf-8') as f:
            dictionary = f.read().split('\n')
        # 字典数据 readDictFile后获得
        self.dict = []
        # 过滤字词数据
        for l in dictionary:
            # limit限制
            if (limit != 0) and (len(self.dict) >= limit):
                break
            # 判断是否有效行
            if ('\t' in l) and (l[0]!="#"):
                columns = l.split("\t")
                # list[[字词, 码]...]
                self.dict.append([columns[0], columns[1]])

    def readSchemaFile(self, path:str):
        """
        读取方案文件
        """

        def parse(spellTrans: list[str]):
            """解析拼运"""
            regex1 = regex.compile(r"^(xform|derive|abbrev|fuzz|xlit|erase)([ \/|])(.*?)\2(.*?)\2?\"?$")
            # 转换捕获组
            regex2 = regex.compile(r"\$(\d+)")
            spellTransList = []
            for l in spellTrans:
                result = regex1.findall(l)
                if len(result) != 0:
                    st = list(result[0])
                    st.pop(1)  # 删掉分隔符号分组
                    # 转换捕获组标记
                    st[2] = regex2.sub(r'\\g<\1>', st[2])
                    spellTransList.append(st)
            return spellTransList
        
        # 解析yaml文件
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.load(f, Loader=yaml.SafeLoader)
            # 方案数据 readSchemaFile后获得
            # algebra
            algebra = schema.get('speller').get('algebra') if schema.get('speller') else None
            # preedit_format
            preedit_format = schema.get('translator').get('preedit_format') if schema.get('translator') else None
        
        # 解析拼运
        self.algebra = parse(algebra) if algebra else None
        self.preedit_format = parse(preedit_format) if preedit_format else None
    
    def algebraAction(self):
        """
        执行一句algebra中的拼运
        """
        # 防空
        if self.algebra == None:
            # 因为有下一列，所有这里要填充，不然显示有问题
            for i in range(len(self.dict)):
                # 填充上一列的码
                self.dict[i].append(self.dict[i][len(self.dict[i]) - 1])
            return

        def substitute(pattern: regex.Pattern, replace: str, string: str):
            """
            替换，返回替换结果
            从 xform & derive 中抽出来
            """
            return ' '.join([self.regexPatch(pattern, replace, c) for c in string.split(' ') ])

        def xform(pattern: str, replace: str):
            """
            xform algebra专用算法
            xform：改写（不保留原形）

            pattern: 正则表达式
            replace: 替换规则
            """
            pattern = regex.compile(pattern)
            for i in range(len(self.dict)):
                # 如果长度等于2，表示还没有转换过
                if len(self.dict[i]) == 2:
                    # 码
                    code = self.dict[i][1]
                    # 按空格切分音节后，进行拼运转换，转换后拼接放入索引2
                    # list[[字, 码, algebra]]
                    # self.dict[i].append(' '.join([pattern.sub(replace, c) for c in code.split(' ') ]))
                    self.dict[i].append(substitute(pattern, replace, code))
                else:
                    # algebra
                    code = self.dict[i][2]
                    # 按空格切分音节后，进行拼运转换，转换后拼接放入索引2
                    # list[[字, 码, algebra]]
                    # self.dict[i][2] = ' '.join([pattern.sub(replace, c) for c in code.split(' ') ])
                    self.dict[i][2] = substitute(pattern, replace, code)
                assert len(self.dict[i]) <= 3
        
        def derive(pattern: str, replace: str):
            """
            derive algebra专用算法
            derive：衍生（保留原型）
            """
            pattern = regex.compile(pattern)
            for i in range(len(self.dict)):
                if len(self.dict[i]) == 2:
                    # 码
                    code = self.dict[i][1]
                else:
                    # algebra
                    code = self.dict[i][2]
                # 衍生/derive
                if pattern.search(code):
                    self.dict.insert((i+1), [None, None, substitute(pattern, replace, code)])

        # 主体
        for i in range(len(self.algebra)):
            """
            a[0]: 操作
            a[1]: 正则
            a[2]: 替换
            """
            # 本条algebra
            a = self.algebra[i]
            if a[0] == "xform":
                xform(a[1], a[2])
            elif a[0] == "xlit":
                self.xlit(a[1], a[2], 2)
            elif a[0] == "derive":
                derive(a[1], a[2])
            print(f"已执行：{a[0]} 正则:{a[1]} 替换:{a[2]}")
            # 显示下条algebra
            if (i+1) < len(self.algebra):
                n = self.algebra[i+1]
                print(f"-> 下一条：{n[0]} 正则:{n[1]} 替换:{n[2]}")
            yield True


    def preeditFormatAction(self):
        """
        执行一句preedit_format中的拼运
        需要在algebra完成后才能使用
        """
        # 防空
        if self.preedit_format == None:
            return

        def xform(pattern: str, replace: str):
            """
            xform preedit_format 专用算法
            xform:改写（不保留原型）
            
            """
            # ======规则转换======
            # 转换音节起始位置标记
            pattern = pattern.replace(r'\<', r"(?<=^|[ '])")
            # 转换音节结束位置标记
            pattern = pattern.replace(r'\>', r"(?=[ ']|$)")
            # 转换\x3为空
            replace = replace.replace(r'\x3', r"")
            # ===================
            # 编译表达式
            pattern = regex.compile(pattern)
            for i in range(len(self.dict)):
                # 如果长度等于3，表示还没用转换过
                if len(self.dict[i]) <= 3:
                    # 当有algebra时选algebra
                    # 当没有时，选择码
                    code = self.dict[i][len(self.dict[i]) - 1]
                    # 替换后添加到索引3
                    # self.dict[i].append(pattern.sub(replace, code))
                    self.dict[i].append(self.regexPatch(pattern, replace, code))
                elif len(self.dict[i]) > 3:
                    # preedit_format
                    code = self.dict[i][3]
                    # 替换后放到索引3
                    # self.dict[i][3] = pattern.sub(replace, code)
                    self.dict[i][3] = self.regexPatch(pattern, replace, code)
                assert len(self.dict[i]) <= 4
        
        # 主体
        for i in range(len(self.preedit_format)):
            """
            p[0]: 操作
            p[1]: 正则
            p[2]: 替换
            """
            # 本条preedit_format
            p = self.preedit_format[i]
            if p[0] == "xform":
                xform(p[1], p[2])
            elif p[0] == "xlit":
                self.xlit(p[1], p[2], 3)
            print(f"已执行：{p[0]} 正则:{p[1]} 替换:{p[2]}")
            # 显示下条preedit_format
            if (i+1) < len(self.preedit_format):
                n = self.preedit_format[i+1]
                print(f"->下一条：{n[0]} 正则:{n[1]} 替换:{n[2]}")
            yield True
            

    def xlit(self, origin: str, result: str, index: int):
        """
        xlit 通用算法
        xlit: 变换（一对一替换）

        origin: 原字符
        result: 目标
        index: 结果放入的索引(列号)
        """
        for i in range(len(self.dict)):
            # 如果长度等于2，表示还没有转换过码
            if len(self.dict[i]) == index:
                # 码/index - 1
                code = self.dict[i][index - 1]
                # 一对一替换，放入索引index
                for j in range(len(origin)):
                    code = code.replace(origin[j], result[j])
                self.dict[i].append(code)
            else:
                # algebra/index
                code = self.dict[i][index]
                # 一对一替换，放入索引index
                for j in range(len(origin)):
                    code = code.replace(origin[j], result[j])
                self.dict[i][index] = code
            assert len(self.dict[i]) <= (index + 1)
    
    def regexPatch(self, compiled : regex.Pattern, repl: str, string: str):
        """
        正则表达式补丁
        修补一些正则表达式规则，以改变 `regex.sub()` 达到预期效果

        compiled: 编译后的正则表达式
        repl: 替换规则
        string: 被替换的字符串
        
        目前：
        1. 元字符，形如\\L \\U \\l \\u \\E （提供较基础的支持）
        """
        # 1. 元字符 - 1
        r1_1 = regex.compile(r'(\\(?:L|U|l|u))\\g<(\d)>(?:\\E)?')    # 替换信息
        r1_2 = regex.compile(r'\\(?:L|U|l|u)\\g<\d>(?:\\E)?')    # 替换整体
        op_group_1 = r1_1.findall(repl)
        op_group_2 = r1_2.findall(repl)
        if op_group_1:
            # 补丁版正则
        
            # 进行regex.search()
            string_groups = []
            t = compiled.search(string)
            while t:
                string_groups.append(t)
                t = compiled.search(string, t.span()[1])

            # 1. 元字符 - 2
            # 遍历匹配的组
            for string_group in string_groups:
                if type(string_group) == regex.Match:
                    string_group = [string_group]
                assert(len(string_group) == len(op_group_1))
                # 组操作
                for i in range(len(op_group_1)):
                    # 元字符操作
                    op = op_group_1[i][0]
                    # 组号/group number
                    gn = int(op_group_1[i][1])
                    # 边界
                    border = string_group[i].regs[gn]
                    # 内容/group content
                    gc = string[border[0] : border[1]]
                    # repl被替换的部分/repl replace old
                    rr = op_group_2[i]
                    

                    if op == "\\L":
                        # 全部小写
                        gc = gc.lower()
                    elif op == "\\l":
                        # 首字母小写
                        gc = gc[0].lower() + gc[1:]
                    elif op == "\\U":
                        # 全部大写
                        gc = gc.upper()
                    elif op == "\\u":
                        # 首字母大写
                        gc = gc[0].upper() + gc[1:]
                    else:
                        print("正则表达式补丁-元字符部分可能有不支持的规则")
                    repl = repl.replace(rr, gc)
            return compiled.sub(repl, string)
        else:
            # 普通正则
            # 太好了~ 这回不用给regex打补丁了
            return compiled.sub(repl, string)
        



if __name__ == "__main__":
    st = SpellTool()

    # 1. 元字符测试
    r1 = regex.compile('^([a-z]*)$')
    result = st.regexPatch(r1, r"\g<1>\t（\U\g<1>\E）", 'aaam')
    print(result)
