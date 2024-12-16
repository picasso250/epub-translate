def split_file_by_empty_lines(input_file, target_size=4000):
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按空行分割
    sections = content.split('\n\n')
    
    current_chunk = []
    current_size = 0
    file_count = 1
    
    # 遍历每个段落
    for section in sections:
        section_size = len(section)
        
        # 如果当前块加上新段落超过目标大小,保存当前块并开始新块
        if current_size + section_size > target_size and current_chunk:
            # 保存当前块
            output_file = f'output_{file_count}.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(current_chunk))
            
            # 重置计数器
            current_chunk = []
            current_size = 0
            file_count += 1
            
        # 添加当前段落到块
        current_chunk.append(section)
        current_size += section_size
    
    # 保存最后一个块
    if current_chunk:
        output_file = f'output_{file_count}.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(current_chunk))

# 使用脚本
split_file_by_empty_lines('c.txt')