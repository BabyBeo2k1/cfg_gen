import javalang 
import networkx as nx
from stmtCFG import buildNode
import stmtCFG
import re
def getLine(node:javalang.ast.Node):
    """
    get line of code for sorting
    waring: not use for extract source code
    """
    # pos=0
    # try:
        
    # except:
    #     print(node)
    return node.position.line
def findData(root):
    """
    FOR DATA FACILITATING ONLY
    find data that used in a block of for, while, do 
    """
    res=[]
    children=None
    if isinstance(root,javalang.ast.Node):
        if isinstance(root,(javalang.tree.MemberReference,javalang.tree.This)):
            return [root]
        elif isinstance(root,javalang.tree.MethodInvocation):
            if not root.qualifier is None:
                res+=[root]
            children=root.children
        else:
            children=root.children
    else:
        children=root
    for child in children:
        if isinstance(child, (javalang.ast.Node, list, tuple)):
            res+=findData(child)
    return res
def containData(var,datalist):
    """
    FOR DATA FACILITATING ONLY
    return if data contain in datalist
    """
    if isinstance(var,javalang.tree.MemberReference):
        for data in datalist:
            if isinstance(data,javalang.tree.MemberReference):
                if data.member==var.member:
                    return True
            if isinstance(data,javalang.tree.MethodInvocation):
                if data.qualifier==var.member:
                    return True
    if isinstance(var,javalang.tree.This):
        for data in datalist:
            if isinstance(data,javalang.tree.This):
                if var.selectors==data.selectors:
                    return True
    if isinstance(var,javalang.tree.MethodInvocation):
        for data in datalist:
            if isinstance(data,javalang.tree.MethodInvocation):
                if data.qualifier==var.qualifier:
                    return True
    return False

def camelCaseSplit(string):
    """
    split camel case java
    """
    strings = [string]
    strings = [re.sub(r"(\b\w)", lambda match: match.group().upper(), s) for s in strings]
    return [x.lower() for x in re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', strings[0])] + re.findall(r'\d+', strings[0])

def isSWUM(method_name_1 : str, method_name_2 : str):
    """
    word model for software
    compare 2 string semantically
    """
    words_1, words_2 = camelCaseSplit(method_name_1), camelCaseSplit(method_name_2)    
    numOfMatches = 0
    words_len = max(len(words_1), len(words_2))
    for word_1, word_2 in zip(words_1, words_2):
        if word_1 == word_2:
            numOfMatches += 1
    if (numOfMatches / words_len) >= 0.5:
        return True
    return False     
    
class Sunit:
    def __init__(self, body : str):
        """
        build CFG for method 
        init:
            self.ast: AST 
            self.cfg: CFG
            self.source_code: String class
        """
        
        cls = "public class Main {\n" + body + "\n}"
        tree = javalang.parse.parse(cls)
        
        self.source_code = cls
        self.ast = tree
        
        method = None
        
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            method = node
            break
        self.method_node=method
        G = nx.DiGraph()
        G.add_node(method)
        prev = [method]
        x=method.body
        for stmt in method.body:
            prev, G = buildNode(G, prev, stmt)
            
        self.cfg = G

    """
        return source code line from node position(Loc)
    """    
    def getSource(self, node : javalang.ast.Node):  
        if node.position == None:
            return ""
            
        for idx, line in enumerate(self.source_code.splitlines()):
            if idx+1 == node.position.line:
                return line
                
    def getSameActionSunit(self):
        """
        get method declaration of the main method
        get all method invocation and compare similarity to the main method name by using SWUM
        """
        res=[]
        method=None
        for node in self.cfg.nodes:
            if isinstance(node,javalang.tree.MethodDeclaration):
                method=node
                break
        for _,node in self.ast.filter(javalang.tree.MethodInvocation):
            if isSWUM(method.name,node.member):
                res+=[node]
        return res
    
    def isIsolated(self,node:javalang.ast.Node):
        """
        check if a node is an extra node that will not be executed in the code
        """
        traverse=list(nx.edge_dfs(self.cfg,self.method_node,'original'))
        for traveled in traverse:
            if node in traveled:
                return False
        return True
    def composeSunit(self):
        """
        get compose first 3 sunit heuristic
        get data sunit from previous heuristic
        get control sunit from previous heuristic
        sort by code line in class
        return list of lines of code
        """
        res=[]
        res+=self.getEndingSunit()
        res+=self.getSameActionSunit()
        res+=self.getVoidReturnSunit()
        heu_data1=[]
        for result in res:
            if not result in heu_data1:
                heu_data1.append(result)
        heu_data1+=self.getDataFacilitatingSunit(heu_data1)
        heu_control1=[]
        for dt in heu_data1:
            if not dt in heu_control1:
                heu_control1.append(dt)
        heu_control1+=self.getControllingSunit(heu_control1)
        heu_data2=[]
        for unit in heu_control1:
            if not unit in heu_data2:
                heu_data2.append(unit)
        heu_data2+=self.getDataFacilitatingSunit(heu_control1)
        # heu_control2=[]
        # for dt in heu_data2:
        #     if not dt in heu_control2:
        #         heu_control2.append(dt)
        # heu_control2+=self.getControllingSunit(heu_control2)
        ret=[]
        for unit in heu_data2:
            if not unit in ret:
                ret.append(unit)
        # prev_len=-1
        # ret=res
        # while repeat>0:
        #     prev_len=len(ret)
        #     res=[]
        #     ret+=self.getDataFacilitatingSunit(ret)
        #     ret+=self.getControllingSunit(ret)
        #     for unit in ret:
        #         if not unit in res:
        #             res.append(unit)
        #     ret=res
        #     repeat-=1
        self.source_code= self.getNewBody(ret)
        
    def getNewBody(self,sunits:javalang.ast.Node):
        """
        remove excesive data and modify source code
        """
        remove_list=[]
        remove_bracket=[]
        pos=[]
        for unit in sunits:
            try:
                pos.append(unit.position.line)
            except:
                continue
        for node in self.cfg.nodes:
            try:
                if not node in sunits and not node.position.line in pos and not isinstance(node,javalang.tree.MethodDeclaration):
                    remove_list.append(node.position.line)
                    if isinstance(node,javalang.tree.IfStatement):
                        if node.then_statement is not None:
                            self.removeBlockBracket(node.then_statement)
                        if node.else_statement is not None:
                            
                            self.removeBlockBracket(node.else_statement)
                            
                    if isinstance(node,(javalang.tree.DoStatement,javalang.tree.ForStatement,javalang.tree.WhileStatement)):
                        if node.body is not None:
                            self.removeBlockBracket(node.body)
                    if isinstance(node,javalang.tree.TryStatement):
                        last_bracket=self.removeTry(node)
                        if node.catches is not None:
                            for catch in node.catches:
                                last_bracket=self.removeCatch(catch,last_bracket+1)
            except:
                continue
        body_lines=self.source_code.split('\n')
        res=[]
        for idx,line in enumerate(body_lines):
            if idx+1 in remove_list or idx==0 or idx==(len(body_lines)-1):
                
                continue
            res.append(line)
        lines=[line for line in res if line.strip()]
        ret='\n'.join(lines)

        return ret.strip()
    def removeCatch(self,catch,last_bracket):
        while self.source_code[last_bracket]!="{":
            if self.source_code[last_bracket]!="\n":
                self.source_code=self.source_code[:last_bracket]+' '+self.source_code[last_bracket+1:]
            last_bracket+=1
        cnt=1
        if self.source_code[last_bracket]!='\n':
            self.source_code=self.source_code[:last_bracket]+' '+self.source_code[last_bracket+1:]
        while cnt >0:
            last_bracket+=1
            if self.source_code[last_bracket]=='{':
                cnt+=1
            if self.source_code[last_bracket]=='}':
                cnt-=1
            if self.source_code[last_bracket]!="\n":
                self.source_code=self.source_code[:last_bracket]+' '+self.source_code[last_bracket+1:]
        return last_bracket


    def removeTry(self,node):
        pos=self.getpos(node)
        while self.source_code[pos]!='{':
            
            x=self.source_code[pos]
            if self.source_code[pos]!='\n':
                self.source_code=self.source_code[:pos]+' '+self.source_code[pos+1:]
            pos+=1
        if self.source_code[pos]!='\n':
            self.source_code=self.source_code[:pos]+' '+self.source_code[pos+1:]
        cnt=1
        
        while cnt>0:
            pos+=1
            if self.source_code[pos]=='{':
                cnt+=1
            if self.source_code[pos]=='}':
                cnt-=1
        if self.source_code[pos]!='\n':
            self.source_code=self.source_code[:pos]+' '+self.source_code[pos+1:]
        return pos
    def getpos(self,node):
        line=node.position.line-1
        col=node.position.column-1
        res=0
        while line>0:
            if self.source_code[res]=='\n':
                line-=1
            res+=1
        while col>0:
            col-=1
            res+=1
        return res
    
    def removeBlockBracket(self,node:javalang.tree.BlockStatement):
        if isinstance(node,javalang.tree.IfStatement):
            return
        
        init=self.getpos(node)
        if self.source_code[init]!="{":
            return
        if self.source_code[init]!='\n':
            
            self.source_code=self.source_code[:init]+' '+self.source_code[init+1:]
        
        cnt=1
        while cnt>0:
            init+=1
            if self.source_code[init]=='{':
                cnt+=1
            if self.source_code[init]=='}':
                cnt-=1
        self.source_code=self.source_code[:init]+' '+self.source_code[init+1:]
        
    def getControllingSunit(self,sunits:list[javalang.ast.Node]):
        """
        input previous heuristic
        return the latest branching statement (if/switch/while/for)
        """
        res=[]
        for _,node in self.ast:
            if isinstance(node,javalang.tree.IfStatement):
                block=[]
                if node.then_statement is not None:
                    then=node.then_statement
                    if isinstance(then,javalang.tree.BlockStatement):
                        block+=then.statements
                    else:
                        block.append(then)
                if node.else_statement is not None:
                    el=node.else_statement
                    
                    if isinstance(el,javalang.tree.BlockStatement):
                        block+=el.statements
                    else:
                        block.append(el)
                for stmt in block:
                    if stmt in sunits:
                        res+=[node]
                        break
            
            elif isinstance(node,javalang.tree.SwitchStatement):
                for case in node.cases:
                    for stmt in case.statements:
                            
                        if stmt in sunits:
                            res+= [node]
                            break
            elif isinstance(node,(javalang.tree.WhileStatement,javalang.tree.ForStatement,javalang.tree.DoStatement)):
                if not isinstance(node.body,javalang.tree.BlockStatement):
                    if isinstance(node.body,list):
                        print("it is list")
                    if node.body in sunits:
                        res+=[node]
                        break
                    else:
                        continue
                for stmt in node.body.statements:
                    
                    if stmt in sunits:
                        res+=[node]
                        break
        return res
    
    def getDataFacilitatingSunit(self,sunits:list[javalang.ast.Node]):
        """
        get data
        """
        datalist=[]
        for node in sunits:
            datalist+=findData(node)
        res=[]
        for _,node in self.ast:
            if isinstance(node,javalang.tree.LocalVariableDeclaration):
                for data in datalist:
                    if isinstance(data,javalang.tree.MemberReference):
                        declarators=node.declarators
                        if any([data.member== dec.name for dec in declarators ]):
                            res.append(node)
                            break
                    if isinstance(data,javalang.tree.MethodInvocation):
                        declarators=node.declarators
                        if any([data.qualifier== dec.name for dec in declarators ]):
                            res.append(node)
                            break
                        if data.qualifier in declarators:
                            res.append(node)
            elif isinstance(node,javalang.tree.StatementExpression):
                if isinstance(node.expression,javalang.tree.Assignment):
                    assign=node.expression
                    if containData(assign.expressionl,datalist):
                        res.append(node)
                if isinstance(node.expression,javalang.tree.MethodInvocation):
                    if containData(node.expression,datalist):
                        res.append(node)
                if isinstance(node.expression,javalang.tree.MemberReference):
                    if containData(node,datalist):
                        res.append(node)
                if isinstance(node.expression,javalang.tree.This):
                    if containData(node,datalist):
                        res.append(node)
        return res
    def getVoidReturnSunit(self):
        """
        get all statement that have method invocation in expression (which is void method)
        """
        res=[]
        for _,node in self.ast.filter(javalang.tree.StatementExpression):
            if isinstance(node.expression,javalang.tree.MethodInvocation):
                
                res+=[node]
        return res
    def getPrevStatement(self,node:javalang.ast.Node):
        if isinstance(node,(javalang.tree.IfStatement,javalang.tree.SwitchStatement,javalang.tree.StatementExpression)):
            return [node]
        elif any(isinstance(pre,(javalang.tree.ForStatement,javalang.tree.WhileStatement,javalang.tree.DoStatement)) for pre in list(self.cfg.predecessors(node))):
            res=[]
            for pre in list(self.cfg.predecessors(node)):
                if isinstance(pre,(javalang.tree.ForStatement,javalang.tree.WhileStatement,javalang.tree.DoStatement)):
                    res+=self.get_end(pre)
            return res
        else:
            return self.getPrevStatement(list(self.cfg.predecessors(node))[0])
    def getEndingSunit(self):
        """
        get all node in cfg that either:
            a return node (if that is void, return previous line)
            a node that direct to no 
        """
        res=[]
        for node in self.cfg.nodes:
            if self.cfg.out_degree(node)==0:
                if self.isIsolated(node):
                    
                    continue
                
                if isinstance(node,(javalang.tree.BreakStatement)) :
                    while all(isinstance(pre,javalang.tree.Statement) for pre in list(self.cfg.predecessors(node))):
                        if len(list(self.cfg.predecessors(node)))>0:
                            
                            node=list(self.cfg.predecessors(node))[0]
                        else: 
                            break
                
                res+=[node]
            elif isinstance(node,javalang.tree.ReturnStatement):
                res+=[node]        
            elif isinstance(node,(javalang.tree.ForStatement,javalang.tree.WhileStatement,javalang.tree.DoStatement)):
                if (all(suc in node.children for suc in list(self.cfg.successors(node)))):
                    res+=self.get_end(node.body)
        return res
    def get_end(self,node):
        
        if isinstance(node,(javalang.tree.BlockStatement)):
            if len(node.statements)>0:

                return self.get_end(node.statements[-1])
            else:
                return self.cfg.predecessors(node)
        elif isinstance(node,javalang.tree.IfStatement):
            res=[]
            if node.then_statement is not None:
                res+=self.get_end(node.then_statement)
            if node.else_statement is not None:
                res +=self.get_end(node.else_statement)
            return res
        elif isinstance(node,javalang.tree.TryStatement):
            res=[]
            if node.finally_block is not None: 
                if len(node.finally_block)>0:
                    return self.get_end(node.finally_block[-1])
                else:
                        
                    res+=self.get_end(node.block[-1])
                    if node.catches is not None:
                        for catch in node.catches:
                            if len(catch.block)>0:
                                res+=self.get_end(catch.block[-1])

            else:
                res+=self.get_end(node.block[-1])
                if node.catches is not None:
                    for catch in node.catches:
                        if len(catch.block)>0:
                            res+=self.get_end(catch.block[-1])
            return res
                        
        elif isinstance(node,(javalang.tree.ForStatement,javalang.tree.WhileStatement,javalang.tree.DoStatement)):
            return self.get_end(node.body)
        elif isinstance(node,javalang.tree.SwitchStatement):
            res=[]
            for case in node.cases:
                if len(case.statements)>0:
                    res+=self.get_end(case.statements[-1])
            return res
            
        else:
            return [node]





            