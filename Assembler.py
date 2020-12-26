# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 18:49:11 2020
@author: Olivier Frechette
Hack Assembler
(nand2tetris Project 6)
"""

# %% Packages and fullbin() function

import sys
import re

## Converts any integer to its 16-bit binary value
def fullbin(i):
    return '0000000000000000'[:18-len(bin(i))]+bin(i)[2:]

# %% Symbol table initialization

## Predefined symbols
variables = {'SP'    :'0000000000000000',
             'LCL'   :'0000000000000001',
             'ARG'   :'0000000000000010',
             'THIS'  :'0000000000000011',
             'THAT'  :'0000000000000100',
             'SCREEN':'0100000000000000',
             'KBD'   :'0110000000000000'}

# Generate virtual registers
for i in range(16): 
    symbol = 'R'+str(i)
    value = fullbin(i)
    variables[symbol]=value

# Initial memory location for new variables
nextVar = 16

# Initialize dictionary for jump labels
labels = {}

## C-instruction mnemonic tables
jumpConditions = {'null':'000',
                  'JGT' :'001',
                  'JEQ' :'010',
                  'JGE' :'011',
                  'JLT' :'100',
                  'JNE' :'101',
                  'JLE' :'110',
                  'JMP' :'111'}

storageSpaces = {'null':'000',
                 'M'   :'001', 
                 'D'   :'010', 
                 'MD'  :'011',
                 'A'   :'100',
                 'AM'  :'101',
                 'AD'  :'110',
                 'AMD' :'111'}

computations = {'0'  :'101010',
                '1'  :'111111',
                '-1' :'111010',
                'D'  :'001100',
                'A'  :'110000',
                '!D' :'001101',
                '!A' :'110001',
                '-D' :'001111',
                '-A' :'110011',
                'D+1':'011111',
                'A+1':'110111',
                'D-1':'001110',
                'A-1':'110010',
                'D+A':'000010',
                'D-A':'010011',
                'A-D':'000111',
                'D&A':'000000',
                'D|A':'010101'}

# %% Parsing

## First code parse (remove whitespace and comments)

def firstParse(code):
    parsedCode = []
    for line in code:
        parsedLine = re.sub(' ','',line) # Remove whitespace
        if parsedLine == '' or parsedLine[0:2] == '//': # Remove empty lines and comment lines
            continue
        parsedLine = re.sub(r'\/\/.*','',parsedLine) # Remove inline comments
        parsedCode.append(parsedLine)
    return parsedCode

##  Second code parse (document and remove labels)

def secondParse(code):
    global labels
    parsedCode = []
    nLabels = 0
    for i,line in enumerate(code):
        if line[0] == '(' and line[-1] == ')': # Identify label lines
            label = re.sub(r'\(|\)','',line)   # Extract label name
            labels[label] = fullbin(i-nLabels) # Document label with line number
            nLabels += 1
            continue
        parsedCode.append(line)
    return parsedCode

# %% Instruction translation

## Check if instruction is valid

## Translate A-Instruction
def aInstr(line):
    global variables
    address = line[1:]
    if address.isdigit():
        instruction = fullbin(int(address))
    elif address in labels:
        instruction = labels[address]
    elif address in variables:
        instruction = variables[address]
    else:
        global nextVar
        variables[address] = fullbin(nextVar)
        nextVar += 1
        instruction = variables[address]

    return instruction

## Translate C-instruction    
def cInstr(line):
    instruction='1110000000000000'
    jmp   = False # Jump instruction
    sto   = False # Store instruction
    mem   = False # Accessing RAM

    # Translate mnemonics and assign to corresponding variables
    splitInstr = re.split('=|;',line)
    if len(splitInstr) == 3:                # sto=comp;jmp -> [[sto],[comp],[jmp]]
        sto  = storageSpaces[splitInstr[0]]
        comp = splitInstr[1]
        jmp  = jumpConditions[splitInstr[2]]
    elif len(splitInstr) == 2 and splitInstr[1] in jumpConditions: # comp;jmp -> [[comp],[jmp]]
        comp = splitInstr[0]
        jmp  = jumpConditions[splitInstr[1]]
    else:                                   # sto=comp -> [[sto],[comp]]
        sto  = storageSpaces[splitInstr[0]]
        comp = splitInstr[1]
        
    # Special case : computation contains M
    if 'M' in comp:
        mem = '1'
        comp = re.sub('M','A',comp)
    
    comp = computations[comp]
    
    # Generate machine language from mnemonics
    instruction = instruction[:4] + comp + instruction[10:]
    
    if jmp:
        instruction = instruction[:-3] + jmp
    if sto:
        instruction = instruction[:-6] + sto + instruction[-3:]
    if mem:
        instruction = instruction[:3] + mem + instruction[4:]
        
    return instruction

# %% Program implementation

## There is an inffeciency in the fact that this program does three full passes
## of the assembly code. The program could probably be improved to only do two
## passes, first parsing the code and saving the labels, then translating the
## parsed code. Because labels can be called and defined at any point, I don't
## think it's possible to go any lower than two passes.

filename = sys.argv[1]
outputfile = re.sub(r'\..*','',filename)+'.hack'

f = open(filename, "r")
code = f.read().splitlines()
f.close()

output = open(outputfile, "w")

code = firstParse(code)
code = secondParse(code)

for line in code:
    if line[0] == '@':
        instruction = aInstr(line)
    else:
        instruction = cInstr(line)
    output.write(instruction+'\n')

