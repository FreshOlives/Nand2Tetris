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

# %% Jack Analyzer

# %% Jack Tokenizer

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

# %% Compilation Engine

class CompilationEngine:
    def __init__(self, inputStream):
        self.dataStream = inputStream
        self.compiledData = []
        self.streamIndex = 0
        self.linesLeft = True
        
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
        
    def compileClassVarDec(self):
        print('\tcompiling classVarDec')
        self.compiledData.append('<classVarDec>')
        
        # Append static/field
        self.writeToken()
        # Append type
        self.writeToken()
        # Append varName
        self.writeToken()
        
        # Compile additional variables
        while self.dataStream[self.streamIndex][1] != ';':
            # Append varName
            self.writeToken()    
        
        # Append ';'
        self.writeToken()
        
        self.compiledData.append('</classVarDec>')
        
    def compileSubroutine(self):
        print('\tcompiling Subroutine')
        self.compiledData.append('<subroutineDec>')
        
        # Append constructor/function/method
        self.writeToken()
        # Append void/type
        self.writeToken()
        # Append subroutineName
        self.writeToken()
        # Append '('
        self.writeToken()
        # Compile parameter list
        self.compileParameterList()
        # Append ')'
        self.writeToken()
        
        # Compile subroutine body
        self.compiledData.append('<subroutineBody>')
        
        # Append '{'
        self.writeToken()
        
        # Compile variable declarations
        while self.dataStream[self.streamIndex][1] == 'var':
            self.compileVarDec()
            
        # Compile statements
        self.compileStatements()
        
        # Append '}'
        self.writeToken()
        
        self.compiledData.append('</subroutineBody>')
        
        self.compiledData.append('</subroutineDec>')
        
    def compileParameterList(self):
        print('\tcompiling parameterList')
        self.compiledData.append('<parameterList>')
        
        # A little lazy, doesn't check at all for syntax errors, then again 
        # none of my code does yet
        while self.dataStream[self.streamIndex][1] != ')':
            # Append type/varName/','
            self.writeToken()    
        
        self.compiledData.append('</parameterList>')
        
    def compileVarDec(self):
        print('\tcompiling varDec')
        self.compiledData.append('<varDec>')
        
        # Append var
        self.writeToken()
        # Append type
        self.writeToken()
        # Append varName
        self.writeToken()
        
        # Compile additional variables
        while self.dataStream[self.streamIndex][1] != ';':
            # Append varName
            self.writeToken()    
        
        # Append ';'
        self.writeToken()
        
        self.compiledData.append('</varDec>')
    
    def compileStatements(self):
        
        self.compiledData.append('<statements>')
        print('\tcompiling statements')
        # While statements remain
        while self.areLinesLeft() and self.dataStream[self.streamIndex][1] in ['let','if','while','do','return']:
            statementKeyword = self.dataStream[self.streamIndex][1]
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
    
    def compileDo(self):
        print('\tcompiling doStatement')
        self.compiledData.append('<doStatement>')
        
        # Append do
        self.writeToken()
        # Subroutine call
        self.compileSubroutineCall()  # VALIDATE
        #Append ';'
        self.writeToken()
        
        self.compiledData.append('</doStatement>')
    
    def compileSubroutineCall(self):
        print('\tcompiling subroutineCall')
        
        # Write subroutineName/className/varName
        self.writeToken()
        if self.dataStream[self.streamIndex][1] == '.':
            # Write .subroutineName
            self.writeToken()
            self.writeToken()
        
        # Append '('
        self.writeToken()
        # Compile expression list
        self.compileExpressionList()
        # Append ')'
        self.writeToken()
    
    def compileLet(self):
        print('\tcompiling letStatement')
        self.compiledData.append('<letStatement>')
        
        # Append do
        self.writeToken()
        # Append variable name
        self.writeToken()
        
        # Case of Array index
        if self.dataStream[self.streamIndex][1] == '[':
            # Append '['
            self.writeToken()
            # Compile expression
            self.compileExpression()
            # Append ']'
            self.writeToken()
        
        # Append '='
        self.writeToken()
        
        # Compile expression
        self.compileExpression()
        
        #Append ';'
        self.writeToken()
        
        self.compiledData.append('</letStatement>')
    
    def compileWhile(self):
        print('\tcompiling whileStatement')
        self.compiledData.append('<whileStatement>')
        
        # Append while
        self.writeToken()
        # Append '('
        self.writeToken()
        # Compile expression
        self.compileExpression()
        # Append ')'
        self.writeToken()
        # Append '{'
        self.writeToken()
        # Compile statements    
        self.compileStatements()
        # Append '}'
        self.writeToken()
        
        self.compiledData.append('</whileStatement>')
    
    def compileReturn(self):
        print('\tcompiling returnStatement')
        self.compiledData.append('<returnStatement>')
        
        # Append return
        self.writeToken()
        # Return expression?
        if self.dataStream[self.streamIndex][1] != ';':
            self.compileExpression()        
        #Append ';'
        self.writeToken()
        
        self.compiledData.append('</returnStatement>')
    
    def compileIf(self):
        print('\tcompiling ifStatement')
        self.compiledData.append('<ifStatement>')
        
        # Append while
        self.writeToken()
        # Append '('
        self.writeToken()
        # Compile expression
        self.compileExpression()
        # Append ')'
        self.writeToken()
        # Append '{'
        self.writeToken()
        # Compile statements    
        self.compileStatements()
        # Append '}'
        self.writeToken()
        
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
        
        self.compiledData.append('</ifStatement>')
    
    def compileExpression(self):
        print('\tcompiling expression')
        self.compiledData.append('<expression>')
        self.compileTerm()
        while self.dataStream[self.streamIndex][1] in CompilationEngine.ops:
            # Write operator
            self.writeToken()
            # Write term
            self.compileTerm()
        self.compiledData.append('</expression>')
    
    def compileTerm(self):
        print('\tcompiling term')
        self.compiledData.append('<term>')
        
        # Unary operators
        if self.dataStream[self.streamIndex][1] in CompilationEngine.unaryOps:
            # Write operator
            self.writeToken()
            # Write term
            self.compileTerm()
        # Integer, string or keyword
        elif self.dataStream[self.streamIndex][0] in ['<integerConstant>','<stringConstant>','keyword']:
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
            else:
                # Write varname
                self.writeToken()
                # Check for array
                if self.dataStream[self.streamIndex][1] == '[':
                    self.writeToken()
                    self.compileExpression()
                    self.writeToken()
                
        self.compiledData.append('</term>')
    
    def compileExpressionList(self):
        print('\tcompiling expressionList')
        self.compiledData.append('<expressionList>')
        
        # Append first expression if applicable
        if self.dataStream[self.streamIndex][1] != ')':
            self.compileExpression()
        # Append additionnal expressions if applicable
        while self.dataStream[self.streamIndex][1] == ',':
            # Append ','
            self.writeToken()
            self.compileExpression()
            
        self.compiledData.append('</expressionList>')

    ops = ['+','-','*','/','&','|','<','>','=','&lt;','&gt;','&amp;']
    unaryOps = ['-','~']

# %% Main program

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
    #output= open(path+'0'+file[:-5]+'Tok.xml', 'w')
    
    entries = []
    
    #output.write('<tokens>')
    while tokenizer.hasMoreTokens():
        tokenizer.advance()
        token = tokenizer.getToken()
        if token != '':
            tokenType = tokenizer.tokenType()
            #output.write('\n\t<'+tokenType+'> '+token+' </'+tokenType+'>')
            entries.append(tokenizer.getEntry())
    
    #output.write('\n</tokens>')
    #output.close()
    
    engine = CompilationEngine(entries)
    engine.compileClass()
    output= open(path+file[:-5]+'.xml', 'w')
    for line in engine.compiledData:
        text = ''
        for entry in line:
            text += entry
        output.write(text+'\n')
    
    output.close()