import re

def process_file(input_file, output_file):
    # 正则匹配指令前缀（如 BIU0: 或 SHU:），不会匹配到标签
    pattern = r"(\b\w+\b)(\s*:.*?)(?:\|\||;)"                          #用于匹配除NOP之外的指令
    pattern_without_wait = r"(?i)(\b\w+\b)\s*:(?!\s*wait)(.*?)(\|\||;)" #用于匹配排除wait指令的指令
    pattern_wait = r"(?i)(\b\w+\b)\s*:(\s*wait)\s+(\d+)"                #用于匹配wait指令
    

    # 用于存储结果，每条指令包含指令内容、行号和列号
    instructions = []
    # 用于存储每列的指令发射槽和对应列号
    inst_slot = {}
    # 行号计数器
    row_cnt = 0
    # 列号计数器
    col_cnt = 0

    # 读取文件内容，读取文件的所有行，并以列表的形式返回，每一行作为一个字符串存储在列表content中
    with open(input_file, 'r', encoding='utf-8') as infile:
        content = infile.readlines()
    
    # 提取指令槽信息和列号，从上到下，从左到右遍历指令，先不考虑wait指令，因为有些wait 0的指令可以不写，这种情况用wait会影响排序
    for line in content:          #遍历每一行，line_num为行索引,从1开始
        matches = re.finditer(pattern_without_wait, line)#匹配非wait指令
        for match in matches:
            slot = match.group(1)               #获取指令槽
            slot = slot.upper()
            if "FALU" in slot:                  #如果 slot 中包含不区分大小写的 "FALU"，替换为 "FMA"
                slot = slot.replace("FALU", "FMA")
            if "FMAC" in slot:                  #如果 slot 中包含不区分大小写的 "FMAC"，替换为 "Tensor"
                slot = slot.replace("FMAC", "TENSOR")
            if slot not in inst_slot:           # 判断是否已经存在相同的 slot
                inst_slot[slot]=({                      # 保存指令槽和列号
                    "col_num": col_cnt,
                    "latency": 0,
                })
                col_cnt += 1                            # 列计数递增
    
    
    # 提取所有指令，并通过维护的行号计数器和指令槽信息添加指令的行号和列号
        # 1. 先注释处理，删除当前行//后的所有内容，删除/**/之间的所有内容
        # 2. 以";"为分割提取一行，匹配当前行所有指令，查询inst_slot表查询其列号和延迟，根据行号计数器和延迟共同决定最终行号
        # 3. 提取完当前行的指令信息后再确认有无wait指令，有则更新inst_slot中的指令槽的latency
        # 4. 处理完一行后行号计数器+1
    with open(input_file, 'r', encoding='utf-8') as infile:
        content = infile.read()  # 读取整个文件内容为一个字符串
    pattern_comment = r"/\*.*?\*/|//.*?$"
    # 使用 re.DOTALL 使 `.` 能匹配换行符，从而匹配多行注释, re.MULTILINE使 $ 匹配每一行的结束，用于 // 注释
    processed_content = re.sub(pattern_comment, '', content, flags=re.DOTALL | re.MULTILINE)
    
    #用分号分割成多行
    lines = processed_content.split(';')
    # 遍历每行，并匹配指令
    for line in lines:
        line = line.strip()  
        line = line + ";"
        matches = re.finditer(pattern, line)
        for match in matches:
            this_slot = match.group(1)
            this_slot = this_slot.upper()
            if "FALU" in this_slot:                  #如果 slot 中包含不区分大小写的 "FALU"，替换为 "FMA"
                this_slot = this_slot.replace("FALU", "FMA")
            if "FMAC" in this_slot:                  #如果 slot 中包含不区分大小写的 "FMAC"，替换为 "Tensor"
                this_slot = this_slot.replace("FMAC", "TENSOR")
            row_num = row_cnt + inst_slot[this_slot]["latency"]#计算该指令的最终行号
            col_num = inst_slot[this_slot]["col_num"]
            instructions.append(
                {
                    "instruction":match.group(1)+match.group(2).strip(),
                    "row_num":row_num,
                    "col_num":col_num,
                }
            )
        row_cnt += 1
        #如果当前行是wait指令行，更新wait指令的latency
        matches = re.finditer(pattern_wait, line)
        for match in matches:
            this_slot = match.group(1)
            this_slot = this_slot.upper()
            if "FALU" in this_slot:                  #如果 slot 中包含不区分大小写的 "FALU"，替换为 "FMA"
                this_slot = this_slot.replace("FALU", "FMA")
            if "FMAC" in this_slot:                  #如果 slot 中包含不区分大小写的 "FMAC"，替换为 "Tensor"
                this_slot = this_slot.replace("FMAC", "TENSOR")
            inst_slot[this_slot]["latency"] = int(match.group(3))


    instructions = sorted(instructions, key=lambda inst: (inst["row_num"], inst["col_num"]))#按照行列排序

    # 根据行列号构建每个指令的字符串表示
    max_line = max(inst["row_num"] for inst in instructions)
    max_col = max(inst["col_num"] for inst in instructions)
    result_lines = [["\t" for _ in range(max_col + 1)] for _ in range(max_line + 1)]

    
    for inst in instructions:
        line_idx = inst["row_num"]
        col_idx = inst["col_num"]
        result_lines[line_idx][col_idx] = inst["instruction"] + "\t"
        #print(inst["instruction"],line_idx, col_idx)

    # 将每一行连接
    aligned_result = ["".join(line) for line in result_lines]

    # 将结果写入输出文件
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("\n".join(aligned_result))


# 示例：读取文件并处理
input_file = "asm_in.txt"
output_file = "excel_output.txt"
process_file(input_file, output_file)
print(f"结果已写入文件: {output_file}")