import javalang
import networkx as nx
import copy
def check_pred(cfg:nx.DiGraph,source,type):
    for pred in list(cfg.predecessors(source)):
        if isinstance(pred,type):
            return pred
        else:
            return check_pred(cfg,pred,type)
def buildNode(cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.ast.Node):
    #interface of build a stmt
    cfgBuilder= stmtCFG()
    res,cfg=cfgBuilder.buildNode(cfg,prev,node)
    return res,cfg
class stmtCFG:
    def buildNode(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.ast.Node):
        #abstract method to build next node
        if isinstance(node,type(None)):
           return prev,cfg
        elif isinstance(node,javalang.tree.IfStatement):
            return self.buildIf(cfg,prev,node)
        elif isinstance(node,javalang.tree.ForStatement):
            return self.buildFor(cfg,prev,node)
        elif isinstance(node,javalang.tree.WhileStatement):
            return self.buildWhile(cfg,prev,node)
        elif isinstance(node,javalang.tree.DoStatement):
            return self.buildDo(cfg,prev,node)
        elif isinstance(node,javalang.tree.ReturnStatement):
            return self.buildReturn(cfg,prev,node)
        elif isinstance(node,javalang.tree.TryStatement):
            return self.buildTry(cfg,prev,node)
        elif isinstance(node,javalang.tree.SwitchStatement):
            return self.buildSwitch(cfg,prev,node)
        elif isinstance(node,javalang.tree.BlockStatement):
            return self.buildBlock(cfg,prev,node)
        
        else:
            return self.buildStmt(cfg,prev,node)
    
    def buildBlock(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.tree.BlockStatement):
        
        for stmt in node.statements:
            if isinstance(stmt,(javalang.tree.BreakStatement)):
                cfg.add_node(stmt)
                for pre in prev:
                    cfg.add_edge(pre,node)
                label=check_pred(cfg,node,(javalang.tree.ForStatement,javalang.tree.DoStatement,javalang.tree.WhileStatement,javalang.tree.SwitchStatement))
                if isinstance(label,javalang.tree.SwitchStatement):
                    return [node],cfg
                cfg.add_edge(stmt,label)
                return [],cfg  
            elif isinstance(stmt,javalang.tree.ContinueStatement):
                cfg.add_node(stmt)
                for pre in prev:
                    cfg.add_edge(pre,node)
                label=check_pred(cfg,node,(javalang.tree.ForStatement,javalang.tree.DoStatement,javalang.tree.WhileStatement))
                if isinstance(label,javalang.tree.ForStatement):
                    cfg.add_edge(node,label.control)
                    label=label.control
                else:
                    cfg.add_edge(node,label.condition)
                    label=label.condition
                return [],cfg            
            else:
                prev,cfg=self.buildNode(cfg,prev,stmt)
        return prev,cfg
    def buildIf(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.tree.IfStatement):
        cfg.add_node(node)
        for pre in prev:
            cfg.add_edge(pre,node)
        prev=[node]
        cfg.add_node(node.condition)
        
        for pre in prev:
            cfg.add_edge(pre,node.condition)
        last_then=[node.condition]
        last_else=[node.condition]
        last_else,cfg=self.buildNode(cfg,last_else,node.else_statement)
        last_then,cfg=self.buildNode(cfg,last_then,node.then_statement)
        res=last_else+last_then
        return res,cfg

    def buildFor(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.tree.ForStatement):
        # if isinstance(node.control,javalang.tree.EnhancedForControl):
        cfg.add_node(node)
        for pre in prev:
            cfg.add_edge(pre,node)
        prev=[node]
        prev,cfg=self.buildNode(cfg,prev,node.control)
        prev,cfg=self.buildNode(cfg,prev,node.body)
        prev,cfg=self.buildNode(cfg,prev,node.control)
        for pre in prev:
            cfg.add_edge(pre,node)
        prev=[node]
        return prev,cfg
        # cfg.add_node(node)
        # for pre in prev:
        #     cfg.add_edge(pre,node)
        # control=node.control
        # condition=control.condition
        # init=control.init
        # update=control.update
        # prev=[node]
        # prev,cfg=self.buildNode(cfg,prev,init)

        # prev,cfg=self.buildNode(cfg,prev,condition)

        # prev,cfg=self.buildNode(cfg,prev,node.body)
        # for up in update:
        #     prev,cfg=self.buildNode(cfg,prev,up)
        # prev,cfg=self.buildNode(cfg,prev,condition)
        # for pre in prev:
        #     cfg.add_edge(pre,node)
        # prev=[node]
        # return prev,cfg
    def buildWhile(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.tree.WhileStatement):
        cfg.add_node(node)
        for pre in prev:
            cfg.add_edge(pre,node)
        prev=[node]
        prev,cfg=self.buildNode(cfg,prev,node.condition)
        prev,cfg=self.buildNode(cfg,prev,node.body)
        prev,cfg=self.buildNode(cfg,prev,node.condition)
        for pre in prev:
            cfg.add_edge(pre,node)
        prev=[node]
        return prev,cfg
    def buildDo(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.tree.DoStatement):
        cfg.add_node(node)
        for pre in prev:
            cfg.add_edge(pre,node)
        prev=[node]
        prev,cfg=self.buildNode(cfg,prev,node.body)
        prev,cfg=self.buildNode(cfg,prev,node.condition)
        for pre in prev:
            cfg.add_edge(pre,node)
        prev,cfg=self.buildNode(cfg,prev,node.body)
        prev=[node]
        return prev,cfg

    def buildReturn(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.tree.ReturnStatement):
        cfg.add_node(node)
        
        for pre in prev:
            cfg.add_edge(pre,node)
        return [],cfg
    def buildTry(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.tree.TryStatement):
        cfg.add_node(node)
        for pre in prev:
            cfg.add_edge(pre,node)
        prev=[node]
        
        if node.resources is not None:
            cfg.add_nodes_from(node.resources)
            for resource in node.resources:
                cfg.add_edge(node,resource)
            prev=node.resources    
        prev_try=prev

        for blk in node.block:
            prev_try,cfg=self.buildNode(cfg,prev_try,blk)
        
        prev_catches=[]
        if node.catches is not None:
            for catch in node.catches:
                prev_catch,cfg=self.buildNode(cfg,prev,catch.parameter)
                for blk in catch.block:
                    prev_catch,cfg=self.buildNode(cfg,prev_catch,blk)
                for pre in prev_catch:
                    prev_catches.append(pre)
        
        prev=[]
        for pre in prev_catches:
            cfg.add_edge(pre,node)
        for pre in prev_try:
            prev.append(pre)
        if node.finally_block is None:
            return prev,cfg
        else:
            for blk in node.finally_block:
                prev,cfg=self.buildNode(cfg,prev,blk)
            return prev,cfg
    def buildStmt(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.ast.Node):
        cfg.add_node(node)
        for pre in prev:
            cfg.add_edge(pre,node)
        return [node],cfg
    def buildSwitch(self,cfg:nx.DiGraph,prev:list[javalang.ast.Node],node:javalang.tree.SwitchStatement):
        cfg.add_node(node)
        for pre in prev:
            cfg.add_edge(pre,node)
        cfg.add_node(node.expression)
        cfg.add_edge(node,node.expression)
        prev=[]
        for case in node.cases:

            pre=[node.expression]
            cfg.add_nodes_from(case.case)
            
            for c in case.case:
                pre,cfg=self.buildNode(cfg,pre,c)
            cfg.add_nodes_from(case.statements)
            for stmt in case.statements:
                pre,cfg=self.buildNode(cfg,pre,stmt)
            for x in pre:
                prev.append(x)
        return prev,cfg