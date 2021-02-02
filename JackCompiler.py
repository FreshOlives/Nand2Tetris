# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 23:23:34 2020

@author: o_fre

Jack Compiler

(nand2tetris projects 10 & 11)
"""

import sys
import os
import re

class JackTokenizer:
    def __init__(self, inputFile, path):
        self.fileName = inputFile
        self.inputFile = open(path+inputFile, 'r').read()
        self.fileIndex = 0;
        self.lastIndex = len(self.inputFile)-1
        
    def hasMoreTokens(self):
        return not(self.fileIndex > self.lastIndex)
    
    def getToken(self):
        if self.tokenType() == 'symbol' and self.token in JackTokenizer.markupSymbols:
            return JackTokenizer.markupSymbols[self.token]
        else:
            return self.token
        
    def getEntry(self):
        tokenType = self.tokenType()
        return ['<'+tokenType+'>',self.getToken(),'</'+tokenType+'>']
    
    def advance(self):
        self.isString = False
        self.token = ''
        if self.hasMoreTokens():
            currChar = self.inputFile[self.fileIndex]
            self.token += currChar
            self.fileIndex += 1
        while self.hasMoreTokens():
            currChar = self.inputFile[self.fileIndex]
            # Strings
            if self.token == '"':
                currChar = self.inputFile[self.fileIndex]
                while currChar != '"':
                    self.token += currChar
                    self.fileIndex += 1
                    currChar = self.inputFile[self.fileIndex]
                self.token = self.token[1:]
                self.fileIndex += 1
                self.isString = True
                break
            
            # Regular comments
            if currChar == '/' and self.inputFile[self.fileIndex-1] == '/': ## WHY IS THIS -1 I AM CONFUSED, but it works
                currChar = self.inputFile[self.fileIndex]
                while currChar != '\n':
                    self.token += currChar
                    self.fileIndex += 1
                    currChar = self.inputFile[self.fileIndex]
                self.fileIndex += 1
                self.advance()
            
            # Block comments
            if currChar == '/' and self.inputFile[self.fileIndex+1] == '*':
                currChar = self.inputFile[self.fileIndex]
                while self.token[-2:] != '*/':
                    self.token += currChar
                    self.fileIndex += 1
                    currChar = self.inputFile[self.fileIndex]
                self.fileIndex += 1
                self.advance()
                
            # Symbols
            if self.token in JackTokenizer.symbols:
                break
            
            if any([self.token in JackTokenizer.delimiters,
                    currChar in JackTokenizer.delimiters]):
                break
            
            if currChar in JackTokenizer.symbols:
                currChar=''
                break
            
            self.token += currChar
            self.fileIndex += 1
        
        if not(self.isString):
            self.token = re.sub(r'\s*','',self.token)
        
        if self.token == '' and self.hasMoreTokens():
            self.advance()
    
    delimiters = ['\n',' ','\t']
    
    symbols = ['{','}','(',')','[',']','.',',',';','~',
                '+','-','*','&','|','<','>','=','/']

    def tokenType(self):
        if self.isString == True:
            return 'stringConstant'
        elif self.token in JackTokenizer.keywords:
            return 'keyword'
        elif self.token in JackTokenizer.symbols:
            return 'symbol'
        elif self.token.isdigit():
            return 'integerConstant'
        else:
            return 'identifier'
        
    def keyWord(self):
        #return '<keyword> '+JackTokenizer.keywords[self.token]+' </keyword>'
        return self.token

    def symbol(self):
        if self.token in JackTokenizer.markupSymbols:
            return JackTokenizer.markupSymbols[self.token]
        else:
            return self.token
    
    def identifier(self):
        return self.token
        
    def intVal(self):
        return self.token
        
    def stringVal(self):
        return self.token

    keywords = {'class'      :'CLASS',
                'constructor':'CONSTRUCTOR',
                'function'   :'FUNCTION',
                'method'     :'METHOD',
                'field'      :'FIELD',
                'static'     :'STATIC',
                'var'        :'VAR',
                'int'        :'INT',
                'char'       :'CHAR',
                'boolean'    :'BOOLEAN',
                'void'       :'VOID',
                'true'       :'TRUE',
                'false'      :'FALSE',
                'null'       :'NULL',
                'this'       :'THIS',
                'let'        :'LET',
                'do'         :'DO',
                'if'         :'IF',
                'else'       :'ELSE',
                'while'      :'WHILE',
                'return'     :'RETURN'}
    
    markupSymbols = {'<':'&lt;',
                      '>':'&gt;',
                      '"':'&quot;',
                      '&':'&amp;'}
    
    
class CompilationEngine:
    def __init__(self, inputStream, filename):                                 ###
        self.filename = filename                                               ###
        self.dataStream = inputStream
        self.compiledData = []
        self.streamIndex = 0
        self.linesLeft = True
        self.classTable = SymbolTable()
        self.subroutineTable = SymbolTable()
        self.writer = VMWriter()
        
    def areLinesLeft(self):
        return self.streamIndex < len(self.dataStream)

    def writeToken(self):
        self.compiledData.append(self.dataStream[self.streamIndex])
        print('\t\t'+str(self.compiledData[-1]))
        self.streamIndex += 1

    def compileClass(self):
        print('\tcompiling Class')
        self.compiledData.append('<class>')
        # Append class
        self.writeToken()
        # Append class name
        self.writeToken()
        #Append '{'
        self.writeToken()
        
        # Handle class body
        while self.dataStream[self.streamIndex][1] != '}':
            if self.dataStream[self.streamIndex][1] in ['static','field']:
                self.compileClassVarDec()
            elif self.dataStream[self.streamIndex][1] in ['constructor','function','method']:
                self.compileSubroutine()
        
        #Append '}'
        self.writeToken()
        self.compiledData.append('</class>')
        print('\tfinished Class')
        
    def compileClassVarDec(self):
        print('\tcompiling classVarDec')
        self.compiledData.append('<classVarDec>')

        # Append static/field
        varKind = self.dataStream[self.streamIndex][1]                         ###
        self.writeToken()
        # Append type
        varType = self.dataStream[self.streamIndex][1]                         ###
        self.writeToken()
        # Append varName
        varName = self.dataStream[self.streamIndex][1]                         ###
        self.writeToken()
        
        # Define variable in class symbol table                                ###
        self.classTable.define(varName, varType, varKind)                      ###
        
        # Compile additional variables
        while self.dataStream[self.streamIndex][1] == ',':                     ###
            # Advance past ','
            self.writeToken()
            # Append varName
            varName = self.dataStream[self.streamIndex][1]                     ###
            self.writeToken()   
            
            # Define variable in  class symbol table                           ###
            self.classTable.define(varName, varType, varKind)                  ###
        
        # Append ';'
        self.writeToken()
        
        self.compiledData.append('</classVarDec>')
        print('\tfinished classVarDec')
        
    def compileSubroutine(self):
        print('\tcompiling Subroutine')
        self.compiledData.append('<subroutineDec>')
        
        # Prepare subroutine table                                             ###
        self.subroutineTable.startSubroutine()                                 ###
        
        # Append constructor/function/method
        funcType = self.dataStream[self.streamIndex][1]                        ###
        self.writeToken()
        # Append void/type
        #returnType = self.dataStream[self.streamIndex][1]                      ###
        self.writeToken()
        # Append subroutineName
        funcName = self.dataStream[self.streamIndex][1]                        ###
        self.writeToken()
        # Append '('
        self.writeToken()
        # add argument position for Obj in methods
        if funcType == 'method':
            self.subroutineTable.define('Object', 'Object', 'arg')
        # Compile parameter list
        self.compileParameterList()
        # Append ')'
        self.writeToken()
        
        # Compile subroutine body
        print('\tcompiling SubroutineBody')
        self.compiledData.append('<subroutineBody>')
        
        # Append '{'
        self.writeToken()
        
        # Initialize number of Local variables
        nLocals = 0                                                            ###
        
        # Compile variable declarations
        while self.dataStream[self.streamIndex][1] == 'var':
            nLocals += self.compileVarDec()                                    ###
        
        
        # Write VM function declaration                                        ###
        self.writer.writeFunction(self.filename+'.'+funcName, nLocals)         ###
        
        if funcType == 'constructor':                                          ###
            print(self.classTable.symbolTable)
            nFields = self.classTable.varCount('field')                        ###
            self.writer.writePush('constant', nFields)                         ###
            self.writer.writeCall('Memory.alloc', 1)                           ###
            self.writer.writePop('pointer', 0)                                 ###
        
        # Method : extract object pointer                                      ###
        if funcType == 'method':                                               ###
            self.writer.writePush('argument', 0)                               ###
            self.writer.writePop('pointer',0)                                  ###
        
        # Compile statements
        self.compileStatements()
        
        # Append '}'
        self.writeToken()
        
        self.compiledData.append('</subroutineBody>')
        print('\tfinished SubroutineBody')
        
        self.compiledData.append('</subroutineDec>')
        print('\tfinished Subroutine')
        
    def compileParameterList(self):
        print('\tcompiling parameterList')
        self.compiledData.append('<parameterList>')
        
        # Initialize number of parameters
        # nParam = 0
        
        while self.dataStream[self.streamIndex][1] != ')':

            while not(self.dataStream[self.streamIndex][1] in [',',')']):      ###
                varType = self.dataStream[self.streamIndex][1]                 ###
                self.writeToken()                                              ###
                varName = self.dataStream[self.streamIndex][1]                 ###
                self.writeToken()                                              ###
                self.subroutineTable.define(varName, varType, 'arg')           ###
            
            if self.dataStream[self.streamIndex][1] != ')':
                self.writeToken()    
        
        self.compiledData.append('</parameterList>')
        print('\tfinished porameterList')
        
        # Return number of parameters compiled                                 ###
        #return int(nParam/2) # Divide by two - counted types and varNames     ###
        
    def compileVarDec(self):
        print('\tcompiling varDec')
        self.compiledData.append('<varDec>')
        
        # Append var
        varKind = self.dataStream[self.streamIndex][1]                         ###
        self.writeToken()
        # Append type
        varType = self.dataStream[self.streamIndex][1]                         ###
        self.writeToken()
        # Append varName
        varName = self.dataStream[self.streamIndex][1]                         ###
        self.writeToken()
        
        # Define variable in subroutine symbol table                           ###
        self.subroutineTable.define(varName, varType, varKind)                 ###
        # Initialize number of variables treated                               ###
        nVars = 1                                                              ###
        
        # Compile additional variables
        while self.dataStream[self.streamIndex][1] == ',':
            # Advance past ','
            self.writeToken()
            # Append varName
            varName = self.dataStream[self.streamIndex][1]                     ###
            self.writeToken()   
            
            # Define variable in subroutine symbol table                       ###
            nVars += 1                                                         ###
            self.subroutineTable.define(varName, varType, varKind)             ###
        
        # Append ';'
        self.writeToken()
        
        self.compiledData.append('</varDec>')
        print('\tfinished varDec')
        return nVars                                                           ###
    
    def compileStatements(self):
        
        self.compiledData.append('<statements>')
        print('\tcompiling statements')
        # While statements remain
        while self.areLinesLeft() and self.dataStream[self.streamIndex][1] in ['let','if','while','do','return']:
            statementKeyword = self.dataStream[self.streamIndex][1]            ###
            # Compile appropriate statement
            if statementKeyword == 'while':
                self.compileWhile()    
            elif statementKeyword == 'let':
                self.compileLet()
            elif statementKeyword == 'if':
                self.compileIf()
            elif statementKeyword == 'do':
                self.compileDo()
            elif statementKeyword == 'return':
                self.compileReturn()
        
        self.compiledData.append('</statements>')
        print('\tfinished statements')
    
    def compileDo(self):
        print('\tcompiling doStatement')
        self.compiledData.append('<doStatement>')
        
        # Append do
        self.writeToken()
        # Subroutine call
        self.compileSubroutineCall()
        #Append ';'
        self.writeToken()
        
        self.writer.writePop('temp', 0)
        
        self.compiledData.append('</doStatement>')
        print('\tfinished doStatement')
    
    def compileSubroutineCall(self):
        print('\tcompiling subroutineCall')
        
        isObj = False                                                          ###
        
        # Write subroutineName/className/varName
        funcName = self.dataStream[self.streamIndex][1]                        ###
        self.writeToken()
        if self.dataStream[self.streamIndex][1] == '.':
            # Write '.'
            objInfo = self.checkForObj(funcName)
            funcName += self.dataStream[self.streamIndex][1]                   ###
            self.writeToken()
            
            print(objInfo)
            if objInfo != None:                                                ###
                isObj = True                                                   ###
                objKind = objInfo[0]                                           ###
                objInd  = objInfo[1]                                           ###
                objType = objInfo[2]                                           ###
                self.objPush(objKind, objInd)                                  ###
                funcName = objType+'.'                                         ###
            
            funcName += self.dataStream[self.streamIndex][1]                   ###
            # Write subroutineName
            self.writeToken()
        else:
            funcName = self.filename + '.' + funcName
            isObj = True
            self.writer.writePush('pointer', 0)
        
        # Append '('
        self.writeToken()
        # Compile expression list
        nArgs = self.compileExpressionList()                                   ###
        # Append ')'
        self.writeToken()
        
        if isObj:                                                              ###
            nArgs += 1                                                         ###
        
        # Write subroutine call to VM code                                     ###
        self.writer.writeCall(funcName, nArgs)                                 ###
        
        print('\tfinished subroutineCall')
        
    def checkForObj(self, objName):
        # print(self.subroutineTable.symbolTable)
        # print(self.classTable.symbolTable)
        if self.subroutineTable.kindOf(objName) != None:                       ###
                objKind = self.subroutineTable.kindOf(objName)                 ###
                objInd = self.subroutineTable.indexOf(objName)                 ###
                objType = self.subroutineTable.typeOf(objName)                 ###
                return [objKind, objInd, objType]                              ###
        elif self.classTable.kindOf(objName) != None:                          ###
                objKind = self.classTable.kindOf(objName)                      ###
                objInd = self.classTable.indexOf(objName)                      ###
                objType = self.classTable.typeOf(objName)                      ###
                return [objKind, objInd, objType]                              ###
        else:                                                                  ###
            return None                                                        ###
        
    def objPush(self, varKind, varInd):
        if varKind == 'static':                                                ###
            self.writer.writePush('static', varInd)                            ###
        elif varKind == 'field':                                               ###
            self.writer.writePush('this', varInd)                              ###
        elif varKind == 'arg':                                                 ###
            self.writer.writePush('argument', varInd)                          ###
        else:                                                                  ###
            self.writer.writePush('local', varInd)                             ###
    
    def compileLet(self):
        print('\tcompiling letStatement')
        self.compiledData.append('<letStatement>')
        
        # Append let
        self.writeToken()
        # Append variable name
        varName = self.dataStream[self.streamIndex][1]                         ### 
        self.writeToken()
        
        # Case of Array index
        isArray = False
        if self.dataStream[self.streamIndex][1] == '[':
            
            isArray = True  ## TODO : DEAL WITH ARRAY CASE
            
            # Append '['
            self.writeToken()
            # Compile expression
            self.compileExpression()
            # Append ']'
            self.writeToken()
            
            # Add index to array base
            self.varPush(varName)
            self.writer.writeArithmetic('add')
        
        # Append '='
        self.writeToken()
        
        # Compile expression
        self.compileExpression()
        
        #Append ';'
        self.writeToken()
        
        # VM Pop to variable                                                   ###
        if isArray:
            self.writer.writePop('temp', 0)
            self.writer.writePop('pointer',1)
            self.writer.writePush('temp', 0)
            self.writer.writePop('that', 0)
        else:
            self.varPop(varName)
        # if self.subroutineTable.kindOf(varName) != None:                       ###
        #     varKind = self.subroutineTable.kindOf(varName)                     ###
        #     varInd = self.subroutineTable.indexOf(varName)                     ###
        # else :                                                                 ###
        #     varKind = self.classTable.kindOf(varName)                          ###
        #     varInd = self.classTable.indexOf(varName)                          ###
            
        # if varKind == 'static':                                                ###
        #     self.writer.writePop('static', varInd)                             ###
        # elif varKind == 'field':                                               ###
        #     self.writer.writePop('this', varInd)                               ###
        # elif varKind == 'arg':                                                 ###
        #     self.writer.writePop('argument', varInd)                           ###
        # else:                                                                  ###
        #     self.writer.writePop('local', varInd)                              ###
        
        self.compiledData.append('</letStatement>')
        print('\tfinished letStatement')
    
    def varPop(self,varName):
        if self.subroutineTable.kindOf(varName) != None:                       ###
            varKind = self.subroutineTable.kindOf(varName)                     ###
            varInd = self.subroutineTable.indexOf(varName)                     ###
        else :                                                                 ###
            varKind = self.classTable.kindOf(varName)                          ###
            varInd = self.classTable.indexOf(varName)                          ###
            
        if varKind == 'static':                                                ###
            self.writer.writePop('static', varInd)                             ###
        elif varKind == 'field':                                               ###
            self.writer.writePop('this', varInd)                               ###
        elif varKind == 'arg':                                                 ###
            self.writer.writePop('argument', varInd)                           ###
        else:                                                                  ###
            self.writer.writePop('local', varInd)                              ###
            
    def varPush(self,varName):
        if self.subroutineTable.kindOf(varName) != None:                       ###
            varKind = self.subroutineTable.kindOf(varName)                     ###
            varInd = self.subroutineTable.indexOf(varName)                     ###
        else :                                                                 ###
            varKind = self.classTable.kindOf(varName)                          ###
            varInd = self.classTable.indexOf(varName)                          ###
            
        if varKind == 'static':                                                ###
            self.writer.writePush('static', varInd)                            ###
        elif varKind == 'field':                                               ###
            self.writer.writePush('this', varInd)                              ###
        elif varKind == 'arg':                                                 ###
            self.writer.writePush('argument', varInd)                          ###
        else:                                                                  ###
            self.writer.writePush('local', varInd)                             ###
    
    def compileWhile(self):
        print('\tcompiling whileStatement')
        self.compiledData.append('<whileStatement>')
        
        # Initialize labels                                                    ###
        loopLabel = 'loopLabel'+str(self.streamIndex)                          ###
        endLabel = 'endLabel'+str(self.streamIndex)                            ###
        
        # Loop label                                                           ###
        self.writer.writeLabel(loopLabel)                                      ###
        
        # Append while
        self.writeToken()
        # Append '('
        self.writeToken()
        # Compile expression
        self.compileExpression()
        
        # Check                                                                ###
        self.writer.writeArithmetic('not')                                     ###
        self.writer.writeIf(endLabel)                                          ###
        
        # Append ')'
        self.writeToken()
        # Append '{'
        self.writeToken()
        # Compile statements    
        self.compileStatements()
        # Append '}'
        self.writeToken()
        
        # Loop                                                                 ###
        self.writer.writeGoto(loopLabel)                                       ###
        # End Label                                                            ###
        self.writer.writeLabel(endLabel)                                       ###
        
        self.compiledData.append('</whileStatement>')
        print('\tfinished whileStatement')
    
    def compileReturn(self):
        print('\tcompiling returnStatement')
        self.compiledData.append('<returnStatement>')
        
        # Append return
        self.writeToken()
        # Return expression?
        if self.dataStream[self.streamIndex][1] != ';':
            self.compileExpression()        
        else:
            # VM write return 0                                                ### Is this really
            self.writer.writePush('constant', 0)                               ### necessary?
        
        #Append ';'
        self.writeToken()
        
        ## VM Writer write return
        self.writer.writeReturn()                                              ###
        
        self.compiledData.append('</returnStatement>')
        print('\tfinished returnStatement')
    
    def compileIf(self):
        print('\tcompiling ifStatement')
        self.compiledData.append('<ifStatement>')
        
        # Initialize unique labels                                             ###
        trueLabel = 'trueLabel'+str(self.streamIndex)                          ###
        falseLabel = 'falseLabel'+str(self.streamIndex)                        ###
        endLabel = 'endLabel'+str(self.streamIndex)                            ###
        
        # Append while
        self.writeToken()
        # Append '('
        self.writeToken()
        # Compile expression
        self.compileExpression()
        # Append ')'
        self.writeToken()
        
        # if so goto true                                                      ###
        self.writer.writeIf(trueLabel)                                         ###
        # else goto false                                                      ###
        self.writer.writeGoto(falseLabel)                                      ###
        # write True Label                                                     ###
        self.writer.writeLabel(trueLabel)                                      ###
        
        # Append '{'
        self.writeToken()
        # Compile statements    
        self.compileStatements()
        # Append '}'
        self.writeToken()
        
        # once true is done goto end                                           ###
        self.writer.writeGoto(endLabel)                                        ###
        #write False Label                                                     ###
        self.writer.writeLabel(falseLabel)                                     ###
        
        # Case of else statement
        if self.dataStream[self.streamIndex][1] == 'else':
            # Append else
            self.writeToken()
            # Append '{'
            self.writeToken()
            # Compile statements    
            self.compileStatements()
            # Append '}'
            self.writeToken()
        
        #write End Label                                                       ###
        self.writer.writeLabel(endLabel)                                       ###
        
        self.compiledData.append('</ifStatement>')
        print('\tfinished ifStatement')
    
    def compileExpression(self):
        print('\tcompiling expression')
        self.compiledData.append('<expression>')
        self.compileTerm()
        while self.dataStream[self.streamIndex][1] in CompilationEngine.ops:
            # Write operator
            operator = self.dataStream[self.streamIndex][1]                    ###
            if operator in CompilationEngine.osOps:                            ###
                operator = CompilationEngine.osOps[operator]                   ###
            else:                                                              ###
                operator = CompilationEngine.ops[operator]                     ###
            self.writeToken()
            # Write term
            self.compileTerm()
            
            #Apply operator                                                    ###
            self.writer.writeArithmetic(operator)                              ### 
        
        self.compiledData.append('</expression>')
        print('\tfinished expression')
    
    def compileTerm(self):
        print('\tcompiling term')
        self.compiledData.append('<term>')
        
        # Unary operators
        if self.dataStream[self.streamIndex][1] in CompilationEngine.unaryOps:
            # Write operator
            operator = self.dataStream[self.streamIndex][1]                    ###
            operator = CompilationEngine.unaryOps[operator]                    ###
            self.writeToken()
            # Write term
            self.compileTerm()
            
            #Apply operator                                                    ###
            self.writer.writeArithmetic(operator)                              ###
            
        # Integer, string or keyword
        elif self.dataStream[self.streamIndex][0] in ['<integerConstant>','<stringConstant>','<keyword>']:
            
            # IntegerConstant                                                  ###
            if  self.dataStream[self.streamIndex][0] == '<integerConstant>':   ###
                value = self.dataStream[self.streamIndex][1]                   ###
                self.writer.writePush('constant', int(value))                  ###
            # StringConstant    
            elif self.dataStream[self.streamIndex][0] == '<stringConstant>':   ###
                value = self.dataStream[self.streamIndex][1]
                numChar = len(value)
                self.writer.writePush('constant', numChar)
                self.writer.writeCall('String.new', 1)
                for character in value:
                    self.writer.writePush('constant', ord(character))
                    self.writer.writeCall('String.appendChar', 2)
            # KeywordConstant                                                  ###
            elif self.dataStream[self.streamIndex][0] == '<keyword>':          ###
                keywordConstant = self.dataStream[self.streamIndex][1]         ###
                if keywordConstant == 'true':                                  ###
                    self.writer.writePush('constant', 0)                       ###
                    self.writer.writeArithmetic('not')                         ###
                elif keywordConstant == 'false' or keywordConstant == 'null':  ###
                    self.writer.writePush('constant', 0)                       ###
                elif keywordConstant == 'this':                                ###
                    self.writer.writePush('pointer', 0)                        ###
            
            self.writeToken()
            
        #Var name or subroutine call
        elif self.dataStream[self.streamIndex][1] == '(':
            # Write '('
            self.writeToken()
            # Compile expression
            self.compileExpression()
            # Write ')'
            self.writeToken()
        else:
            # Check for subroutine call
            if self.dataStream[self.streamIndex+1][1] in ['.','(']:
                self.compileSubroutineCall()
            # Check for array
            elif self.dataStream[self.streamIndex+1][1] == '[':
                varName = self.dataStream[self.streamIndex][1]                 ###
                self.writeToken()
                # Write '['
                self.writeToken()
                # Write expression
                self.compileExpression()
                # Write ']'
                self.writeToken()
                
                self.varPush(varName)
                self.writer.writeArithmetic('add')
                self.writer.writePop('pointer', 1)
                self.writer.writePush('that',0)
                
            else:
                # Write varname
                varName = self.dataStream[self.streamIndex][1]                 ###
                self.writeToken()
                # # Check for array
                # if self.dataStream[self.streamIndex][1] == '[':
                #     # Write '['
                #     self.writeToken()
                #     # Write expression
                #     self.compileExpression()
                #     # Write ']'
                #     self.writeToken()
                
                self.varPush(varName)
                # if self.subroutineTable.kindOf(varName) != None:               ###
                #     varKind = self.subroutineTable.kindOf(varName)             ###
                #     varInd = self.subroutineTable.indexOf(varName)             ###
                # else :                                                         ###
                #     varKind = self.classTable.kindOf(varName)                  ###
                #     varInd = self.classTable.indexOf(varName)                  ###
                    
                # if varKind == 'static':                                        ###
                #     self.writer.writePush('static', varInd)                    ###
                # elif varKind == 'field':                                       ###
                #     self.writer.writePush('this', varInd)                      ###
                # elif varKind == 'arg':                                         ###
                #     self.writer.writePush('argument', varInd)                  ###
                # else:                                                          ###
                #     self.writer.writePush('local', varInd)                     ###
        
        self.compiledData.append('</term>')
        print('\tfinished term')
    
    def compileExpressionList(self):
        print('\tcompiling expressionList')
        self.compiledData.append('<expressionList>')
        
        # Initialize nArgs
        nArgs = 0                                                              ###
        
        # Append first expression if applicable
        if self.dataStream[self.streamIndex][1] != ')':
            nArgs += 1                                                         ###
            self.compileExpression()
        # Append additionnal expressions if applicable
        while self.dataStream[self.streamIndex][1] == ',':
            # Append ','
            self.writeToken()
            nArgs += 1                                                         ###
            self.compileExpression()
            
        self.compiledData.append('</expressionList>')
        print('\tfinished expressionList')
        # Return number of arguments compiled                                  ###
        return nArgs                                                           ###
                

    ops = {'+':'add',
           '-':'sub',
           '*':None,
           '/':None,
           '&':'and',
           '|':'or',
           '<':'lt',
           '>':'lt',
           '=':'eq',
           '&lt;':'lt',
           '&gt;':'gt',
           '&amp;':'and'}
    
    osOps = {'*':'call Math.multiply 2','/':'call Math.divide 2'}
    
    unaryOps = {'-':'neg','~':'not'}


class SymbolTable:
    
    def __init__(self):
        self.symbolTable = {}      # {name : [type, kind, index]}
        self.counts = {'static':0,
                        'field':0,
                          'arg':0,
                          'var':0}
        
    def startSubroutine(self):
        print('startingSubroutine')
        self.symbolTable = {}      # {name : [type, kind, index]}
        self.counts = {'static':0,
                        'field':0,
                          'arg':0,
                          'var':0}
        
    def define(self, varName, varType, varKind):
        print('Defining '+varName+' ('+varType+', '+varKind+')')
        self.symbolTable[varName] = [varType, varKind, self.counts[varKind]]
        self.counts[varKind] += 1
        
    def varCount(self, varKind):
        return self.counts[varKind]
        
    def typeOf(self, varName):
        return self.symbolTable[varName][0]
    
    def kindOf(self, varName):
        if varName in self.symbolTable:
            return self.symbolTable[varName][1]
        else:
            return None

    def indexOf(self, varName):
        return self.symbolTable[varName][2]     

class VMWriter: 
    
    def __init__(self):
        self.writtenData = []

    def getData(self):
        return self.writtenData

    def writePush(self, segment, index):
        entry = 'push ' + segment + ' ' + str(index)
        self.writtenData.append(entry)
        
    def writePop(self, segment, index):
        entry = 'pop ' + segment + ' ' + str(index)
        self.writtenData.append(entry)
        
    def writeArithmetic(self, command):
        entry = command
        self.writtenData.append(entry)
        
    def writeLabel(self, label):
        entry = 'label ' + label
        self.writtenData.append(entry)
        
    def writeGoto(self, label):
        entry = 'goto ' + label
        self.writtenData.append(entry)
        
    def writeIf(self, label):
        entry = 'if-goto ' + label
        self.writtenData.append(entry)
        
    def writeCall(self, name, nArgs):
        entry = 'call ' + name + ' ' + str(nArgs)
        self.writtenData.append(entry)
        
    def writeFunction(self, name, nLocals):
        entry = 'function ' + name + ' ' + str(nLocals)
        self.writtenData.append(entry)
        
    def writeReturn(self):
        entry = 'return'
        self.writtenData.append(entry)
        
    #def close()

# %% Jack Compiler

filenames = []
target = sys.argv[1]
isDirectory = not(target[-5:] == '.jack')

if isDirectory:
    path = target + '/' if target[-1] != '/' else target
    for file in os.listdir(target):
        if file[-5:] == '.jack':
            filenames.append(file)
else:
    path = re.match(r'.*[\/\\]',target).group(0) if re.match(r'.*[\/\\]',target) != None else ''
    filenames.append(re.sub(r'.*[\/\\]','',target))


for file in filenames:
    print('\nCompiling '+file)
    tokenizer = JackTokenizer(file,path)
    
    entries = []
    
    while tokenizer.hasMoreTokens():
        tokenizer.advance()
        token = tokenizer.getToken()
        if token != '':
            tokenType = tokenizer.tokenType()
            entries.append(tokenizer.getEntry())
    
    engine = CompilationEngine(entries,file[:-5])
    engine.compileClass()
    output= open(path+file[:-5]+'.xml', 'w')
    for line in engine.compiledData:
        text = ''
        for entry in line:
            text += entry
        output.write(text+'\n')
    
    VMCode = engine.writer.getData()                                           ###
    output= open(path+file[:-5]+'.vm', 'w')
    for line in VMCode:
        output.write(line+'\n')
    
    output.close()