import re

def process_file(input_file, output_file):
    # 正则匹配指令前缀（如 BIU0: 或 SHU:），\b表示单词边界，\w+表示一个或多个字母、数字或下划线
    pattern = r"(\b\w+\b)\s*:"

    # 用于存储结果，每条指令包含指令内容、行号和列号
    instructions = []

    # 读取文件内容，读取文件的所有行，并以列表的形式返回，每一行作为一个字符串存储在列表content中
    with open(input_file, 'r', encoding='utf-8') as infile:
        content = infile.readlines()

    # 提取指令，并保存其行号、列号
    for line_num, line in enumerate(content, start=1):#遍历每一行，line_num为行索引,从1开始
        columns = line.split('\t')                        #将每一行按照\t分割，返回一个子字符串列表columns，注意如果存在n个连续的\t则会产生n-1个空字符串，能保留所在列的信息
        for col_num, column in enumerate(columns):        #遍历子字符串列表columns，获取每个子字符串，col_num为列索引，从0开始
            matches = re.finditer(pattern, column)             #在字符串 column 中查找所有与正则表达式 pattern 匹配的内容，
            for match in matches:
                start_pos = match.end()                         #获取当前匹配结果的结束位置
                instruction = column[start_pos:].strip()        #从匹配结束位置到列的末尾，提取后续的字符串，去掉字符串两端的多余空白字符
                # 检查指令内容是否以分号结束，如果是，则去掉
                if instruction.endswith(";"):  
                    instruction = instruction.rstrip(";")  # 去掉尾部的分号
                full_instruction = match.group(0) + instruction #拼接匹配结果和其后续的字符串，组成指令

                instructions.append({                            #保存指令、行号、列号
                    "instruction": full_instruction.strip(),
                    "line": line_num,
                    "column": col_num
                })
    print(instructions)

    # 找出每列的最小行号
    min_line_numbers = {}
    for inst in instructions:
        col = inst["column"]
        line = inst["line"]
        if col not in min_line_numbers or line < min_line_numbers[col]:
            min_line_numbers[col] = line

    # 让每条指令的行号减去该列的最小行号,添加wait指令
    wait_instructions = []
    for inst in instructions:
        col = inst["column"]
        match = re.match(r"mfetch\s*:", inst["instruction"], flags=re.IGNORECASE)
        if match:
            continue
        inst["line"] = inst["line"] - min_line_numbers[col] + 1
        if(inst["line"] == 1):
            matches = re.finditer(pattern, inst["instruction"])
            for match in matches:
                wait_inst = match.group(0) + "wait " + str(min_line_numbers[col]-1) 
                col_num = col
                wait_instructions.append({                            
                    "instruction": wait_inst.strip(),
                    "line": 0,
                    "column": col_num
                })

    instructions = wait_instructions + instructions
    instructions = sorted(instructions, key=lambda inst: (inst["line"], inst["column"]))#按照行列排序
    #print(instructions)

    # 找出最大的行号和列号
    max_line = max(inst["line"] for inst in instructions)
    max_col = max(inst["column"] for inst in instructions)

        

    # 找出每列的最大指令长度
    max_lengths = {}
    for inst in instructions:
        col = inst["column"]
        length = len(inst["instruction"] + " ||")
        if col not in max_lengths or length > max_lengths[col]:
            max_lengths[col] = length

    #print(max_lengths)

    # 计算每列前面所有列的最大指令长度之和
    cumulative_lengths = [0] * (max_col + 1)
    for col in range(1, max_col + 1):
        cumulative_lengths[col] = cumulative_lengths[col - 1] + max_lengths.get(col - 1, 0)
    
    #print(cumulative_lengths)
    # 初始化结果列表，每一行是一个列表
    result_lines = [["" for _ in range(max_col + 1)] for _ in range(max_line + 1)]

    # 记录每行指令中的最右边指令的列id
    max_col_idxs = [0] * (max_line + 1)
    for inst in instructions:
        line_idx = inst["line"] 
        col_idx = inst["column"]
        max_col_idxs[line_idx] = max(max_col_idxs[line_idx], col_idx)

    

    # 按行号和列号的顺序遍历指令
    for inst in instructions:
        line_idx = inst["line"]
        col_idx = inst["column"]
        # 计算该指令左边需要添加的空格数，左边添加的空格是为了填充“空指令”
        prev_line_length = sum(len(result_lines[line_idx][i]) for i in range(col_idx))
        left_spaces = cumulative_lengths[col_idx] - prev_line_length
        right_spaces = max_lengths[col_idx] - len(inst["instruction"]+" ||")
        #print(left_spaces, line_idx, col_idx)
        # 在指令右边和左边添加空格，右边添加空格是为了本列对齐最长指令
        if max_col_idxs[line_idx] == col_idx:
            result_lines[line_idx][col_idx] = inst["instruction"] + ";"
        else:
            result_lines[line_idx][col_idx] = inst["instruction"] + " " * right_spaces + " ||"
        
        #result_lines[line_idx][col_idx] = inst["instruction"].ljust(max_lengths[col_idx])
        result_lines[line_idx][col_idx] = " " * left_spaces + result_lines[line_idx][col_idx]
        
        #print(result_lines[line_idx][col_idx])

    # 对于空行，添加NOP指令
    for line in result_lines:
        is_empty = all(cell == "" for cell in line)
        if is_empty:
            line[0] = "NOP;"

    # 把wait指令行的FALU换成FMA，FMAC换成Tensor
    #result_lines[0] = [re.sub(r"FMAC(\d+):", r"Tensor\1:", elem) for elem in result_lines[0]]
    result_lines[0] = [re.sub(r"FALU(\d+)(\s*):", r"FMA\1\2: ", elem, flags=re.IGNORECASE) for elem in result_lines[0]]
    
    for i, elem in enumerate(result_lines[0]):
        match = re.match(r"FMAC(\d+)(\s*):", elem, flags=re.IGNORECASE)
        if match:
            result_lines[0][i] = re.sub(r"FMAC(\d+)(\s*):", r"Tensor\1\2:", elem, flags=re.IGNORECASE)
            # 去掉最后两个空格
            result_lines[0][i] = result_lines[0][i][:-4] + "||"
            

    # 将每一行用制表符连接，生成最终的对齐结果
    aligned_result = [" ".join(line) for line in result_lines]

    # 将结果写入输出文件
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("\n".join(aligned_result))


# 示例：读取文件并处理
input_file = "excel_in.txt"
output_file = "asm_output.txt"
process_file(input_file, output_file)
print(f"结果已写入文件: {output_file}")