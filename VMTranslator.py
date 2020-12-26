# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 13:25:18 2020
@author: Olivier Frechette
Hack VM translator
(nand2tetris project 7)
"""

import sys
import re
import os

# %% Parser Module

class codeParser:
    def __init__(self, filename):
        self.filename = re.sub(r'.*[\/\\]','',filename)
        self.inputFile = open(filename, 'r').read().splitlines()
        self.nLines = len(self.inputFile)
        self.nCurrLine = 0
        self.commandsLeft = True
        
    def hasMoreCommands(self):
        return self.commandsLeft
        
    def advance(self):
        unparsedLine = self.inputFile[self.nCurrLine] # Read next line
        if self.nCurrLine == self.nLines-1: # Check if this is the last line
            self.commandsLeft = False
        unparsedLine = re.sub(r'^ | $|','',re.sub(r'[\t ]+',' ',unparsedLine)) # Remove whitespace
        unparsedLine = re.sub(r' ?\/\/.*','',unparsedLine) # Remove comments
        self.currentLine = re.split(r' ',unparsedLine) # Split line into components
        if self.currentLine == [''] and self.commandsLeft == True: # If line is now empty, advance
            self.nCurrLine += 1
            self.advance()
        else:
            self.nCurrLine += 1
        
    def commandType(self):
        return codeParser.commands[self.currentLine[0]]
    
    def getCommand(self):
        return self.currentLine
        
    # Command dictionary
    commands = {'push'    :'C_PUSH',
                'pop'     :'C_POP',
                'label'   :'C_LABEL',
                'goto'    :'C_GOTO',
                'if-goto' :'C_IF',
                'function':'C_FUNCTION',
                'return'  :'C_RETURN',
                'call'    :'C_CALL',
                'add'     :'C_ARITHMETIC',
                'sub'     :'C_ARITHMETIC',
                'neg'     :'C_ARITHMETIC',
                'eq'      :'C_ARITHMETIC',
                'gt'      :'C_ARITHMETIC',
                'lt'      :'C_ARITHMETIC',
                'and'     :'C_ARITHMETIC',
                'or'      :'C_ARITHMETIC',
                'not'     :'C_ARITHMETIC'}
    
    
# %% Code writer Module

class codeWriter:
    def __init__(self, outputFile):
        self.outputname = outputFile
        self.output = open(outputFile, 'w')
        
    def setFileName(self, fileName):
        self.filename = fileName
    
    def writeInit(self):
        self.output.writelines(['@256\n',
                                'D=A\n',
                                '@SP\n',
                                'M=D\n'])
        self.writeCall('Sys.init','0',0)
    
    def writeArithmetic(self, command):
        self.output.write('// '+command+'\n')
        self.output.writelines(['@SP\n',
                                'A=M-1\n'])
        
        if command in codeWriter.unaryArith:
            self.output.write(codeWriter.unaryArith[command])
            return
        
        self.output.writelines(['D=M\n',
                                '@SP\n',
                                'M=M-1\n',
                                'A=M-1\n'])
        
        if command in codeWriter.binaryArith:
            self.output.write(codeWriter.binaryArith[command])
            return
        elif command in codeWriter.compArith:
            self.output.writelines(['D=D-M\n',
                                    '@comp'+str(codeWriter.nCompares)+'T\n',
                                    codeWriter.compArith[command],
                                    '@0\n',
                                    'D=!A\n',
                                    '@comp'+str(codeWriter.nCompares)+'End\n',
                                    '0;JMP\n',
                                    '(comp'+str(codeWriter.nCompares)+'T)\n',
                                    '@0\n',
                                    'D=A\n',
                                    '(comp'+str(codeWriter.nCompares)+'End)\n',
                                    '@SP\n',
                                    'A=M-1\n',
                                    'M=D\n'])
            codeWriter.nCompares += 1
            return
             
    def writePushPop(self, command, segment, index):
        self.output.write('// '+command+' '+segment+' '+index+'\n')
        # Optimize this section by starting with a push/pop branching instead
        # of splitting by memory segment, then adding the common push/pop code
        # after the segment-specific addresssing. Lotta repeated code here.
        if segment == 'constant':
            self.output.writelines(['@'+index+'\n',
                                    'D=A\n',
                                    '@SP\n',
                                    'A=M\n',
                                    'M=D\n',
                                    '@SP\n',
                                    'M=M+1\n'])
        elif segment in codeWriter.segmentPointers:
            if command == 'pop':
                self.output.writelines(['@'+codeWriter.segmentPointers[segment]+'\n',
                                        'D=M\n',
                                        '@'+index+'\n',
                                        'D=A+D\n',
                                        '@13\n',
                                        'M=D\n',
                                        '@SP\n',
                                        'M=M-1\n',
                                        'A=M\n',
                                        'D=M\n',
                                        '@13\n',
                                        'A=M\n',
                                        'M=D\n'])
            elif command == 'push':
                self.output.writelines(['@'+codeWriter.segmentPointers[segment]+'\n',
                                        'D=M\n',
                                        '@'+index+'\n',
                                        'A=A+D\n',
                                        'D=M\n',
                                        '@SP\n',
                                        'A=M\n',
                                        'M=D\n',
                                        '@SP\n',
                                        'M=M+1\n'])
        elif segment == 'temp':
            if command == 'pop':
                self.output.writelines(['@5\n',
                                        'D=A\n',
                                        '@'+index+'\n',
                                        'D=A+D\n',
                                        '@13\n',
                                        'M=D\n',
                                        '@SP\n',
                                        'M=M-1\n',
                                        'A=M\n',
                                        'D=M\n',
                                        '@13\n',
                                        'A=M\n',
                                        'M=D\n'])
            elif command == 'push':
                self.output.writelines(['@5\n',
                                        'D=A\n',
                                        '@'+index+'\n',
                                        'A=A+D\n',
                                        'D=M\n',
                                        '@SP\n',
                                        'A=M\n',
                                        'M=D\n',
                                        '@SP\n',
                                        'M=M+1\n'])
        elif segment == 'static':
            if command == 'pop':
                self.output.writelines(['@SP\n',
                                        'M=M-1\n',
                                        'A=M\n',
                                        'D=M\n',
                                        '@'+self.filename+'.'+index+'\n',
                                        'M=D\n'])
            elif command == 'push':
                self.output.writelines(['@'+self.filename+'.'+index+'\n',
                                        'D=M\n',
                                        '@SP\n',
                                        'A=M\n',
                                        'M=D\n',
                                        '@SP\n',
                                        'M=M+1\n'])
        elif segment == 'pointer':
            if command == 'pop':
                self.output.writelines(['@SP\n',
                                        'M=M-1\n',
                                        'A=M\n',
                                        'D=M\n',
                                        '@'+codeWriter.pointers[index]+'\n',
                                        'M=D\n'])
            if command == 'push':
                self.output.writelines(['@'+codeWriter.pointers[index]+'\n',
                                        'D=M\n',
                                        '@SP\n',
                                        'A=M\n',
                                        'M=D\n',
                                        '@SP\n',
                                        'M=M+1\n'])
    
    def writeLabel(self, label):
        self.output.write('// label '+self.filename+'$'+label+'\n')
        self.output.write('('+self.filename+'$'+label+')\n')
        
    def writeGoto(self, label):
        self.output.write('// goto '+self.filename+'$'+label+'\n')
        self.output.writelines(['@'+self.filename+'$'+label+'\n',
                                '0;JMP\n'])
        
    def writeIf(self, label):
        self.output.write('// if-goto '+self.filename+'$'+label+'\n')
        self.output.writelines(['@SP\n',
                                'M=M-1\n',
                                'A=M\n',
                                'D=M\n',
                                '@'+self.filename+'$'+label+'\n',
                                'D;JNE\n'])
    
    def writeCall(self, functionName, numArgs, nLine):
        self.output.write('// call '+functionName+' '+numArgs+'\n')
        returnLabel = self.filename+'$'+functionName+'$return'+str(nLine)
        # Push return address
        self.output.writelines(['@'+returnLabel+'\n',
                                'D=A\n',
                                '@SP\n',
                                'A=M\n',
                                'M=D\n',
                                '@SP\n',
                                'M=M+1\n'])
        # Push caller LCL
        self.output.writelines(['@LCL\n',
                                'D=M\n',
                                '@SP\n',
                                'A=M\n',
                                'M=D\n',
                                '@SP\n',
                                'M=M+1\n'])
        # Push caller ARG
        self.output.writelines(['@ARG\n',
                                'D=M\n',
                                '@SP\n',
                                'A=M\n',
                                'M=D\n',
                                '@SP\n',
                                'M=M+1\n'])
        # Push caller THIS
        self.writePushPop('push', 'pointer', '0')
        # Push caller THAT
        self.writePushPop('push', 'pointer', '1')
        # Set callee ARG
        self.output.writelines(['@SP\n',
                                'D=M\n',
                                '@'+str(int(numArgs)+5)+'\n',
                                'D=D-A\n',
                                '@ARG\n',
                                'M=D\n'])
        # Set callee LCL
        self.output.writelines(['@SP\n',
                                'D=M\n',
                                '@LCL\n',
                                'M=D\n'])
        # Goto function
        self.output.writelines(['@'+functionName+'\n',
                                '0;JMP\n'])
        # Declare label for return address
        self.output.write('('+returnLabel+')\n')
        
    def writeReturn(self):
        self.output.write('// return\n')
        # FRAME = LCL
        self.output.writelines(['@LCL\n',
                                'D=M\n',
                                '@13\n',
                                'M=D\n'])
        # RET = *(FRAME-5)
        self.output.writelines(['@13\n',
                                'D=M\n',
                                '@5\n',
                                'A=D-A\n',
                                'D=M\n',
                                '@14\n',
                                'M=D\n'])
        # *ARG = POP()
        self.output.writelines(['@SP\n',
                                'A=M-1\n',
                                'D=M\n',
                                '@ARG\n',
                                'A=M\n',
                                'M=D\n'])
        # SP = ARG+1, 
        self.output.writelines(['@ARG\n',
                                'D=M+1\n',
                                '@SP\n'
                                'M=D\n'])
        # THAT = *(FRAME-1), THIS = *(FRAME-2), ARG = *(FRAME-3), LCL = *(FRAME-4)
        for i,label in enumerate(['THAT','THIS','ARG','LCL']):
            self.output.writelines(['@13\n',
                                    'D=M\n',
                                    '@'+str(i+1)+'\n',
                                    'A=D-A\n',
                                    'D=M\n',
                                    '@'+label+'\n',
                                    'M=D\n'])
        # goto RET
        self.output.writelines(['@14\n',
                                'A=M\n',
                                '0;JMP\n'])
        
    def writeFunction(self, functionName, numLocals):
        self.output.write('('+functionName+')\n')
        for i in range(int(numLocals)):
                self.writePushPop('push', 'constant', '0')
        
    def finish(self):
        self.output.writelines(['// Program End\n',
                                '(programEnd)\n',
                                '@programEnd\n',
                                '0;JMP'])
        self.output.close()
    
    nCompares = 0
    
    binaryArith = {'add':'M=D+M\n',
                   'sub':'M=D-M\nM=-M\n',
                   'and':'M=D&M\n',
                   'or' :'M=D|M\n'}                 
    
    unaryArith = {'neg':'M=-M\n',
                  'not':'M=!M\n'}
    
    compArith = {'eq':'D;JNE\n',
                 'gt':'D;JGE\n',
                 'lt':'D;JLE\n'}
    
    segmentPointers = {'local'   :'LCL',
                       'this'    :'THIS',
                       'that'    :'THAT',
                       'argument':'ARG'}
    
    pointers = {'0':'THIS',
                '1':'THAT'}


# %% Main program

filenames = []
parsers = []

target = sys.argv[1]
if target[-3:] == '.vm':
    parsers.append(codeParser(target))
    output = target[:-3] + '.asm'
else:
    path = target + '/'
    filenames = os.listdir(target)
    for file in filenames:
        if file[-3:] == '.vm':
            parsers.append(codeParser(path+file))
    output = path + target + '.asm'

writer = codeWriter(output)

if len(parsers) > 1:
    writer.setFileName('Init')
    writer.writeInit()

for parser in parsers:
    commandsLeft = True
    writer.setFileName(parser.filename)
    while commandsLeft:
        parser.advance()
        commandType = parser.commandType()
        command = parser.getCommand()
        if commandType == 'C_ARITHMETIC':
            writer.writeArithmetic(command[0])
        elif commandType in ['C_PUSH','C_POP']:
            writer.writePushPop(command[0], command[1], command[2])
        elif commandType == 'C_LABEL':
            writer.writeLabel(command[1])
        elif commandType == 'C_GOTO':
            writer.writeGoto(command[1])
        elif commandType == 'C_IF':
            writer.writeIf(command[1])
        elif commandType == 'C_FUNCTION':
            writer.writeFunction(command[1], command[2])
        elif commandType == 'C_RETURN':
            writer.writeReturn()
        elif commandType == 'C_CALL':
            if len(command) == 3:
                writer.writeCall(command[1], command[2], parser.nCurrLine)
            else:
                writer.writeCall(command[1], '0', parser.nCurrLine)
        commandsLeft = parser.hasMoreCommands()

writer.finish()
    