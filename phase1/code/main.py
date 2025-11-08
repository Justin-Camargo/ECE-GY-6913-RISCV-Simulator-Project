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
    
    def readInstr(self, ReadAddress):
        #read instruction memory
        # Assumes all the instructions have a uniform format
        start_row = int(int(ReadAddress, 16)/8)
        instruction = ""
        end_row = 0
        if start_row < len(self.IMem):
            end_row = start_row+4
        else:
            end_row = len(self.IMem)
        for i in range(start_row, end_row, 1):
            instruction += self.IMem[i]
        
        if instruction == '':
            return instruction
        else:
            instruction = hex(int(instruction,2)) 
        
            # Returns hex value
            return instruction
        
    
    def getOpCode(self, instruction_bin):
        return '0b' + instruction_bin[-7:]
    
    def separateRInstr(self, instruction_bin):
        func7 = '0b' + instruction_bin[-32:-25]
        rs2 = '0b' + instruction_bin[-25:-20]
        rs1 = '0b' + instruction_bin[-20:-15]
        func3 = '0b' + instruction_bin[-15:-12]
        rd = '0b' + instruction_bin[-12:-7]
        
        return [func3, func7, rd, rs1, rs2]
        pass
    
    def separateIInstr(self, instruction_bin):
        immed = '0b' + instruction_bin[-32:-20]
        rs1 = '0b' + instruction_bin[-20:-15]
        func3 = '0b' + instruction_bin[-15:-12]
        rd = '0b' + instruction_bin[-12:-7]
        
        return [func3, rd, rs1, immed]
        pass
    
    def separateSBInstr(self, instruction_bin):
        immed_2 = '0b' + instruction_bin[-32:-25]
        rs2 = '0b' + instruction_bin[-25:-20]
        rs1 = '0b' + instruction_bin[-20:-15]
        func3 = '0b' + instruction_bin[-15:-12]
        immed_1 = '0b' + instruction_bin[-12:-7]
        
        return [func3, rs2, rs1, immed_2, immed_1]
        pass
    
    def separateJInstr(self, instruction_bin):
        immed = '0b' + instruction_bin[-32:-12]
        rd = '0b' + instruction_bin[-12:-7]

        return [rd, immed]
        pass
        
class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "\\dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def readDataMem(self, ReadAddress):
        #read data memory
        # start_row = int(int(ReadAddress, 16)/8)
        start_row = round(ReadAddress/8)
        memory_val = ""
        for i in range(start_row, start_row + 4, 1):
            memory_val += self.DMem[i]
        memory_val = hex(int(memory_val,2)) 
        
        # Returns hex value
        return memory_val
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
        # Assuming Reg_addr is base 10
        # Reg_addr_dec = int('0x' + str(Reg_addr), 16)
        
        return self.Registers[Reg_addr]
        pass
    
    def writeRF(self, Reg_addr, Wrt_reg_data):
        if not isinstance(Reg_addr, int):
            raise ValueError("The register address is not an integer.")
        # Assuming Reg_addr is hex
        # Reg_addr_dec = int('0x' + str(Reg_addr), 16)
        
        self.Registers[Reg_addr] = Wrt_reg_data
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
        
    def executeRInstr(self, r_instruction_list):
        func3 = r_instruction_list[0]
        func7 = r_instruction_list[1]
        # rd = r_instruction_list[2]
        rd_int = int(r_instruction_list[2], 2)
        rs1_int = int(r_instruction_list[3], 2)
        rs2_int = int(r_instruction_list[4], 2)
        
        if func3 == '0b000':
            if func7 == '0b0000000':
                sum_var = self.addSignedNums(self.formatMemVal(self.myRF.readRF(rs1_int)), self.formatMemVal(self.myRF.readRF(rs2_int))) 
                self.myRF.writeRF(rd_int, sum_var)
                print("Writing sum to register: {r_instruction_list[2]}")
            else:
                sub_var = self.addSignedNums(self.formatMemVal(self.myRF.readRF(rs1_int)), self.formatMemVal(self.myRF.readRF(rs2_int)))
                self.myRF.writeRF(rd_int, sub_var)
                print("Writing to difference to register: {r_instruction_list[2]}")
        elif func3 == '0b100':
            # Computes XOR between two registers converts the output to hex and pads it
            self.myRF.writeRF(rd_int, self.padHexVal(hex(int(self.myRF.readRF(rs1_int), 16)^int(self.myRF.readRF(rs2_int), 16))))
            print("Writing XOR to register: {r_instruction_list[2]}")
        elif func3 == '0b110':
            # Computes OR between two registers converts the output to hex and pads it
            self.myRF.writeRF(rd_int, self.padHexVal(hex(int(self.myRF.readRF(rs1_int), 16)|int(self.myRF.readRF(rs2_int), 16))))
            print(f"Writing OR to register: {r_instruction_list[2]}")
        else:
            print('This R type instruction is not able to be executed with this RISC-V core.')
        return
        
    def executeIInstr(self, i_instruction_list):
        func3 = i_instruction_list[0]
        rd_int = int(i_instruction_list[1], 2)
        rs1_hex = hex(int(i_instruction_list[2], 2))
        rs1_int = int(i_instruction_list[2], 2)
        # print(f'rs1_int is {rs1_int}')
        immed_bin = i_instruction_list[3]
        immed_hex = hex(int(i_instruction_list[3], 2))
        # print(type(immed_bin), immed_bin)
        immed_hex_byte_addressed = hex(round(int(i_instruction_list[3], 2)/4))
        
        if func3 == '0b000':
            # AddI
            sum_val = self.addSignedNums(self.formatMemVal(self.myRF.readRF(rs1_int)),self.getSignExtVal(immed_hex))
            self.myRF.writeRF(rd_int, sum_val)
            print(f'adding immediate value {immed_hex} to {rs1_hex} and writing to {i_instruction_list[1]}')
            print('\n')
        elif func3 == '0b010':
            # LW
            address_sum = self.addSignedNums(rs1_hex,self.getSignExtVal(immed_hex_byte_addressed))
            # converted_sum = int(address_sum[2:])
            data_mem = self.formatMemVal(self.ext_dmem.readDataMem(address_sum))
            self.myRF.writeRF(rd_int, data_mem)
            print(f'Writing to address {'0x' + str(rd_int)} with value at address {address_sum}')
            print(f'Written data is: {data_mem}')
            print('')
        elif func3 == '0b100':
            # XORI
            print('XORI')
            val_1 = int(self.formatMemVal(self.myRF.readRF(rs1_int)), 16)
            val_2 = int(self.formatMemVal(self.getSignExtVal(immed_hex)), 16)
            comparison = val_1^val_2
            comparison_hex = hex(comparison)
            self.myRF.writeRF(rd_int, comparison_hex)
        elif func3 == '0b110':
            # ORI
            print('ORI')
            comparison = int(self.formatMemVal(self.myRF.readRF(rs1_int)), 16)|int(self.formatMemVal(self.getSignExtVal(immed_hex)), 16)
            self.myRF.writeRF(rd_int, hex(comparison))
        elif func3 == '0b111':
            # ANDI
            print('ANDI')
            comparison = int(self.formatMemVal(self.myRF.readRF(rs1_int)), 16)&int(self.formatMemVal(self.getSignExtVal(immed_hex)), 16)
            self.myRF.writeRF(rd_int, hex(comparison))
        return
        
    #FIXME: Need to complete this method
    # - Need to properly construct sign extended immediate value to be saved
    def executeSInstr(self, s_instruction_list):
        rs2_hex = hex(int(s_instruction_list[1], 2))
        rs1_int = int(s_instruction_list[2], 2)
        # immed_2 = s_instruction_list[3]
        # immed_1 = s_instruction_list[4]
        # immed_comb_bin = immed_2+immed_1[2:]
        immed_comb_hex_byte_addressed = hex(round(int(s_instruction_list[3]+s_instruction_list[4][2:], 2)/4)) 
        
        reg_mem = self.myRF.readRF(int(self.addSignedNums(rs2_hex, immed_comb_hex_byte_addressed)[2:]))
        self.ext_dmem.writeDataMem(rs1_int, reg_mem)
        return
    
    def executeJInstr(self, j_instruction_list):
        
        pass
    
    def executeBInstr(self, b_instruction_list):
        func3 = b_instruction_list[0]
        rs2_hex = hex(int(b_instruction_list[1], 2))
        rs1_hex = hex(int(b_instruction_list[2], 2))[2:]
        immed_2 = b_instruction_list[3]
        immed_1 = b_instruction_list[4]
        immed_comb_bin = immed_2+immed_1[2:]
        immed_comb_hex_byte_addressed = hex(round(int(immed_comb_bin, 2)/4)) 
        
        if func3 == '0b000':
            # BEQ
            if(rs1_hex == rs2_hex):
                # PC = PC + sign_ext(imm) 
                self.nextState["PC"] = self.addSignedNums(hex(self.nextState["PC"]), immed_comb_hex_byte_addressed) 
                print("Branching to instruction: ")
        elif func3 == '0b001':
            # BNE
            if(rs1_hex != rs2_hex):
                # PC = PC + sign_ext(imm) 
                self.nextState["PC"] = self.addSignedNums(hex(self.nextState["PC"]), immed_comb_hex_byte_addressed) 
                print("Branching to instruction: ")
        pass
    
    def getTwosComplement(self, value_hex):
        comparison = '0x'
        for i in range(len(value_hex)-2):
            comparison += 'F'
        inverted_val = int(value_hex,16)^int(comparison, 16)
        complement = inverted_val + 1
        complement_hex = hex(int(str(complement)))
        return complement_hex
    
    def getSignExtVal(self, value_hex):
        sign_extension = ''
        if int(value_hex[2], 16) < 8:
            for i in range(0, 8-len(value_hex[2:])):
                sign_extension == '0'
            return value_hex[0:2] + sign_extension + value_hex[2:]
        else:
            for i in range(0, 8-len(value_hex[2:])):
                sign_extension += 'f'
            return value_hex[0:2] + sign_extension + value_hex[2:]
        return
    
    def addSignedNums(self, val_1_hex, val_2_hex):
        ans = 0
        if int(val_1_hex[2], 16) < 8 and int(val_2_hex[2], 16) < 8: #Both positive
            ans = hex(int(val_1_hex, 16) + int(val_2_hex, 16))
            if(len(ans) == 10 and int(ans[2], 16) > 7):
                print('Addition overflow')                
        elif int(val_1_hex[2], 16) < 8  and int(val_2_hex[2], 16) >= 8: #1 pos., 2 neg.
            ans = hex(int(val_1_hex, 16) + int(self.getTwosComplement(val_2_hex), 16))
        elif int(val_1_hex[2], 16) >= 8  and int(val_2_hex[2], 16) < 8: #1 neg., 2 pos.
            ans = hex(int(self.getTwosComplement(val_1_hex), 16) + int(val_2_hex, 16))
        else:
            ans = hex(int(self.getTwosComplement(val_1_hex), 16) + int(self.getTwosComplement(val_2_hex, 16)))
            
        ans = self.padHexVal(ans)[0:10] #Only keeping 32 bits/8 bytes with 0x prefix
        return ans
    
    def formatMemVal(self, mem_val):
        """ Checks type of mem_val and returns a hex string"""
        if type(mem_val) == str and mem_val[0:2] == '0x':
            return mem_val
        elif type(mem_val) == str and mem_val[0:2] == '0b':
            return hex(int(mem_val, 2))
        else: #Assumes memory is int with base 16
            return '0x' + str(mem_val)
    
    def padHexVal(self, val_hex):
        val_padded = '0x'
        for i in range(8-len(val_hex[2:])):
            val_padded += '0'
        val_padded += val_hex[2:]
        #return padded hex value
        return val_padded
        pass
    
    def padBinVal(self, val_bin):
        val_padded = '0b'
        for i in range(32-len(val_bin[2:])):
            val_padded += '0'
        val_padded += val_bin[2:]
        return val_padded
        pass
            

class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "\\SS_", imem, dmem)
        self.opFilePath = ioDir + "\\StateResult_SS.txt"
            
    def step(self):
        reg_address = hex(self.state.IF["PC"]*8)
        instruction_hex_unpadded = imem.readInstr(reg_address)
        
        self.state.IF["PC"] += 4
        self.nextState.IF["PC"] += 4
        
        if(instruction_hex_unpadded != ''):
            instruction_hex = self.padHexVal(instruction_hex_unpadded) #hex
            instruction_bin = self.padBinVal(bin(int(imem.readInstr(reg_address), base=16)))
            opcode = imem.getOpCode(instruction_bin)
            print(f'Padded cycle {self.cycle} in binary is {instruction_bin} with length of {len(instruction_bin)}')
            # print(f'The opcode of instruction {i} is {opcode}')
            instr_type = self.getInstrType(opcode)
            print(f'Register on cycle{self.cycle} is: \n{self.myRF.Registers}')
            # print(f'Type of item in register on cycle {self.cycle} is {type(self.myRF.Registers[0])}')
            match instr_type:
                case 'R':
                    print('R instruction')
                    r_instruction_list =  imem.separateRInstr(instruction_bin)
                    self.executeRInstr(r_instruction_list)
                case 'I':
                    print('I instruction')
                    i_instruction_list = imem.separateIInstr(instruction_bin)
                    self.executeIInstr(i_instruction_list)
                case 'J':
                    print('J instruction')
                    # print(f'RF values: {self.myRF.Registers}')
                    [rd, immed] = imem.separateJInstr(instruction_bin)
                case 'B':
                    print('B instruction')
                    # [func3, rs2, rs1, immed_2, immed_1] = imem.separateSBInstr(instruction_bin)
                    b_instruction_list = imem.separateSBInstr(instruction_bin)
                    self.executeBInstr(b_instruction_list)
                case 'S':
                    print('S instruction')
                    # [func3, rs2, rs1, immed_2, immed_1] = imem.separateSBInstr(instruction_bin)
                    s_instruction_list = imem.separateSBInstr(instruction_bin)
                    self.executeSInstr(s_instruction_list)
                case _:
                    print('Halt instruction')
                    self.halted = True
        else:
            self.halted = True
        print('')
        # self.halted = True
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
        else:
            break
        # if not fsCore.halted:
        #     fsCore.step()

        # if ssCore.halted and fsCore.halted:
        #     break
    
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()
