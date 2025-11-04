# -*- coding: utf-8 -*-
"""
Created on Sun Oct 12 16:43:06 2025

@author: Justin Camargo
"""

import os
import argparse

MemSize = 1000 # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.

class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        
        with open(ioDir + "\\imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]
    
    # FIXME: Need to start at ReadAddress <JRC, p:2>
    def readInstr(self, ReadAddress):
        #read instruction memory
        # Assumes all the instructions have a uniform format
        start_row = int(int(ReadAddress, 16)/8)
        instruction = ""
        for i in range(start_row, start_row + 4, 1):
            instruction += self.IMem[i]
        instruction = hex(int(instruction,2)) 
        
        return instruction
        pass
    
    def padHexInstr(self, instruction):
        instruction_padded = '0x'
        for i in range(8-len(instruction[2:])):
            instruction_padded += '0'
        instruction_padded += instruction[2:]
        #return padded hex value
        return instruction_padded
        pass
    
    def padBinInstr(self, instruction):
        instruction_padded = '0b'
        for i in range(32-len(instruction[2:])):
            instruction_padded += '0'
        instruction_padded += instruction[2:]
        return instruction_padded
        pass
    
    def getOpCode(self, instruction_bin):
        return '0b' + instruction_bin[-7:]
    
    def getFunc3(self, instruction_bin):
        func3 = '0b' + instruction_bin[-14:-11]
        return func3
    
    def getFunc7(self, instruction_bin):
        return instruction_bin[0:9]
        pass
    
    def separateRInst(self, instruction_bin):
        func7 = '0b' + instruction_bin[-32:-25]
        rs2 = '0b' + instruction_bin[-25:-20]
        rs1 = '0b' + instruction_bin[-20:-15]
        func3 = '0b' + instruction_bin[-15:-12]
        rd = '0b' + instruction_bin[-12:-7]
        
        return [func3, func7, rd, rs1, rs2]
        
class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "\\dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def readInstr(self, ReadAddress):
        #read data memory
        start_row = int(int(ReadAddress, 16)/8)
        instruction = ""
        for i in range(start_row, start_row + 4, 1):
            instruction += self.DMem[i]
        instruction = hex(int(instruction,2)) 
        
        # Returns hex value
        return instruction
        pass
        
    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
        self.DMem[Address] = WriteData
        pass
                     
    def outputDataMem(self):
        resPath = self.ioDir + "\\" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])

class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = [0x0 for i in range(32)]
    
    def readRF(self, Reg_addr):
        if not isinstance(Reg_addr, int):
            raise ValueError("The register address is not an integer.")
        # Assuming Reg_addr is hex
        Reg_addr_dec = int(Reg_addr, 16)
        
        return self.Registers[Reg_addr_dec]
        pass
    
    def writeRF(self, Reg_addr, Wrt_reg_data):
        if not isinstance(Reg_addr, int):
            raise ValueError("The register address is not an integer.")
        # Assuming Reg_addr is hex
        Reg_addr_dec = int(Reg_addr, 16)
        
        self.Registers[Reg_addr_dec] = Wrt_reg_data
        pass
         
    def outputRF(self, cycle):
        op = ["-"*70+"\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        op.extend([str(val)+"\n" for val in self.Registers])
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": False, "Instr": 0}
        self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0, 
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0}
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0, 
                   "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}

class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem

class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "\\SS_", imem, dmem)
        self.opFilePath = ioDir + "\\StateResult_SS.txt"

    def step(self):
        # Your implementation
        # Get the number of instructions we will execute
        num_instr = int(len(imem.IMem)/4)
        # print(f'number of instructions = {num_instr}')
        # Loop through instructions and execute each instruction:
        instr_count = 0
        for i in range(num_instr):
            reg_address = hex(instr_count*32)
            instruction_hex = imem.padHexInstr(imem.readInstr(reg_address)) #hex
            instruction_bin = imem.padBinInstr(bin(int(instruction_hex, base=16)))
   
            opcode = imem.getOpCode(instruction_bin)
            print(f'Padded instruction {i} in binary is {instruction_bin}')
            # print(f'The opcode of instruction {i} is {opcode}')
            instr_type = self.getInstrType(opcode)
            match instr_type:
                case 'R':
                    print('R instruction')
                    [func3, func7, rd, rs1, rs2] = imem.separateRInst(instruction_bin)
                    print(func7)
                    print(rs2)
                    print(rs1)
                    print(func3)
                    print(rd)
                case 'I':
                    print('I instruction')
                    func3 = imem.getFunc3(instruction_bin)
                    func7 = imem.getFunc7(instruction_bin)
                case 'J':
                    print('J instruction')
                case 'B':
                    print('B instruction')
                case 'S':
                    print('S instruction')
                case _:
                    print('Halt instruction')
                
            instr_count += 1
                
            # Based on properties of instruction, add, subtract, etc.
            

        self.halted = True
        if self.state.IF["nop"]:
            self.halted = True
            
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
            
        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1
        
    def getInstrType(self, opcode):
        if opcode == '0b1101111':
            return 'J'
        elif opcode == '0b0110011':
            #add, sub, and, etc. need to check func3 and func7 now
            return 'R'
        elif opcode == '0b0010011' or opcode == '0b0000011':
            #immediate operations
            return 'I'
        elif opcode == '0b1100011':
            #branching operations
            return 'B'
        elif opcode == '0b0100011':
            # Storing word:
            return 'S'
        elif opcode == '0b1111111':
            return 'H'

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "\\FS_", imem, dmem)
        self.opFilePath = ioDir + "\\StateResult_FS.txt"

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------
        
        
        
        # --------------------- MEM stage --------------------
        
        
        
        # --------------------- EX stage ---------------------
        
        
        
        # --------------------- ID stage ---------------------
        
        
        
        # --------------------- IF stage ---------------------
        
        self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True
        
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        
        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

if __name__ == "__main__":
    relative_path = "iodir/"
    absolute_path = os.path.abspath(relative_path)

    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default=absolute_path, type=str, help='Directory for IO data')
    args = parser.parse_args()
    ioDir = os.path.abspath(args.iodir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)
        
    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        if not ssCore.halted:
            ssCore.step()
        
        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()
