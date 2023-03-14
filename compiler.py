import sys

class Compiler:
    file_name = ""
    raw_instruction_result = []
    instruction_result = []
    memory_result = []
    compiled_instruction_result = []
    compiled_memory_result = []
    branches = {}
    memory_address = {}
    memory_content = []
    instruction = {
        "NOP": "000000",
        "STR": "100000",
        "LDR": "100001",
        "ADD": ["000001", "010001"],
        "SUB": ["000010", "010010"],
        "LSL": "010011",
        "LSR": "010100",
        "MOV": ["001111", "011111"],
        "B": "110000",
        "CBZ": "110011",
        "CBNZ": "110001",
        "CMP": "110010",
        "B.EQ": "110100",
        "B.LT": "111000",
        "B.GT": "111100",
    }

    def __init__(self, file_name):
        self.file_name = file_name
        try:
            with open(self.file_name) as f:
                self.raw_instruction_result = [line.rstrip() for line in f]
                if ".data" in self.raw_instruction_result:
                    self.memory_result = self.raw_instruction_result[self.raw_instruction_result.index(".data")+1:]
                    self.instruction_result = self.raw_instruction_result[:self.raw_instruction_result.index(".data")]
                else:
                    self.instruction_result = self.raw_instruction_result
        except IOError as e:
            raise FileNotFoundError("Unable to find file")

    @staticmethod
    def isInteger(s):
        return s.isnumeric() or (s[0] == "-" and s[1:].isnumeric())

    @staticmethod
    def registerToBin(r):
        if r[0].upper() != "X":
            raise Exception(r + " is not a valid register!")
        if not r[1].isnumeric() or len(r) > 2 or int(r[1]) > 7:
            raise Exception(r + " is not a valid register!")
        return "0" * (3 - len(bin(int(r[1]))[2:])) + bin(int(r[1]))[2:]

    @staticmethod
    def intToBin(b):
        return bin(int(b) & (2 ** 8 - 1))[2:] if int(b) < 0 else "0" * (8 - len(bin(int(b))[2:])) + bin(int(b))[2:]

    @staticmethod
    def is_branch(i):
        return i[-1] == ":"

    def get_branches(self):
        line = 0
        for i in self.instruction_result:
            itr = i.replace(",", "").replace("[", "").replace("]", "").split()
            if itr and self.is_branch(itr[0]):
                self.branches[itr[0][:-1]] = line
            elif itr:
                line += 1

    def compile_instruction(self):
        result = []
        for i in self.instruction_result:
            machine_code = ""
            itr = i.replace(",", "").replace("[", "").replace("]", "").split()
            if itr and self.is_branch(itr[0]):
                itr = itr[1:]
            if itr:
                itr[0] = itr[0].upper()
                if itr[0] == "NOP":
                    machine_code = "0"*20
                elif itr[0] == "STR":
                    machine_code = self.instruction[itr[0]] + self.registerToBin(itr[1]) + self.registerToBin(itr[2])
                    if len(itr) == 4:
                        machine_code += self.intToBin(itr[3])
                elif itr[0] == "LDR":
                    machine_code = self.instruction[itr[0]] + self.registerToBin(itr[1]) + self.registerToBin(itr[2])
                    if len(itr) == 4:
                        machine_code += self.intToBin(itr[3])
                elif itr[0] in ["ADD", "SUB"]:
                    if self.isInteger(itr[-1]):
                        machine_code = self.instruction[itr[0]][1] + self.registerToBin(itr[1]) + self.registerToBin(itr[2]) + self.intToBin(itr[3])
                    else:
                        machine_code = self.instruction[itr[0]][0] + self.registerToBin(itr[1]) + self.registerToBin(itr[2]) + self.registerToBin(itr[3]) + "00000"
                elif itr[0] in ["LSL", "LSR"]:
                    machine_code = self.instruction[itr[0]] + self.registerToBin(itr[1]) + self.registerToBin(itr[2]) + self.intToBin(itr[3])
                elif itr[0] == "MOV":
                    if self.isInteger(itr[-1]):
                        machine_code = self.instruction[itr[0]][1] + self.registerToBin(itr[1]) + "000" + self.intToBin(itr[2])
                    else:
                        machine_code = self.instruction[itr[0]][0] + self.registerToBin(itr[1]) + "000" + self.registerToBin(itr[2]) + "00000"
                elif itr[0] == "B":
                    machine_code = self.instruction[itr[0]] + "000000" + self.intToBin(self.branches[itr[1]])
                elif itr[0] in ["CBZ", "CBNZ"]:
                    machine_code = self.instruction[itr[0]] + self.registerToBin(itr[1]) + "000" + self.intToBin(self.branches[itr[2]])
                elif itr[0] == "CMP":
                    machine_code = self.instruction[itr[0]] + "000" + self.registerToBin(itr[1]) + self.registerToBin(itr[2]) + "00000"
                elif itr[0] in ["B.EQ", "B.LT", "B.GT"]:
                    machine_code = self.instruction[itr[0]] + "000000" + self.intToBin(self.branches[itr[1]])
                elif itr[0] == "ADR":
                    if itr[2] not in self.memory_address:
                        raise Exception("Error: " + itr[2] + " not defined in memory!")
                    else:
                        machine_code = self.instruction["MOV"][1] + self.registerToBin(itr[1]) + "000" + self.intToBin(self.memory_address[itr[2]])
                else:
                    raise Exception("Unknown instruction: " + itr[0])
                machine_code += "0"*(20-len(machine_code))

                if len(machine_code) == 20:
                    self.compiled_instruction_result.append("0" * (5 - len("{0:0>4X}".format(int(machine_code, 2)))) + "{0:0>4X}".format(int(machine_code, 2)))
                else:
                    raise Exception("An error has occurred!")

    def get_compiled_instructions(self):
        self.compile_instruction()
        first_digit = ["0", "8"]
        second_digit = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]
        iNum = 0

        try:
            with open("instruction.txt", "w") as f:
                result = ["v3.0 hex words addressed"]
                for i in second_digit:
                    for j in first_digit:
                        str_builder = ""
                        for ins in range(8):
                            if iNum >= len(self.compiled_instruction_result):
                                str_builder += " 00000"
                            else:
                                str_builder += " " + self.compiled_instruction_result[iNum]
                                iNum += 1
                        result.append("\n" + i + j + ":" + str_builder)

                f.writelines(result)
        except IOError as e:
            raise FileNotFoundError("Unable to find file")

    def compile_memory(self):
        mem_index = 0
        for i in self.memory_result:
            if len(i.split()) > 1:
                mem_result = i.split()
                for e in mem_result[1:]:
                    if not self.isInteger(e):
                        raise Exception(e + " is not numeric!")
                    else:
                        bin = self.intToBin(e)
                        self.memory_content.append("0" * (2 - len("{0:0>2X}".format(int(bin, 2)))) + "{0:0>2X}".format(int(bin, 2)))
                    self.memory_address[mem_result[0]] = mem_index
                mem_index += len(mem_result[1:])

    def get_compiled_memory(self):
        self.compile_memory()
        first_digit = ["0", "8"]
        second_digit = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]
        iNum = 0

        try:
            with open("memory.txt", "w") as f:
                result = ["v3.0 hex words addressed"]
                for i in second_digit:
                    for j in first_digit:
                        str_builder = ""
                        for ins in range(8):
                            if iNum >= len(self.memory_content):
                                str_builder += " 00"
                            else:
                                str_builder += " " + self.memory_content[iNum]
                                iNum += 1
                        result.append("\n" + i + j + ":" + str_builder)

                f.writelines(result)
        except IOError as e:
            raise FileNotFoundError("Unable to find file")

def run(filename):
    file_name = filename
    compiler = Compiler(file_name)
    compiler.get_branches()
    compiler.get_compiled_memory()
    compiler.get_compiled_instructions()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Command usage compiler.py <filename>")
    else:
        run(sys.argv[1])
        print("Done!")

