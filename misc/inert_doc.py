import io

DOC_WRAP ="""# ============================================================================="""
DOC_START="""# -----------------------------------------------------------------------------"""

# 打开文件
file = open("./src/tarpitd.py","r+")

# 读取文件内容
content = file.read()

# 找到两个 "MARK_HERE" 标记的位置
start = content.index(DOC_WRAP)
start = content.index("tarpitd.py.1",start)
start = content.index(DOC_START,start) + len(DOC_START)
end = content.index(DOC_WRAP,start)

print(f"{start},{end}")

# 如果找到了两个标记，就替换它们之间的内容
if start != -1 and end != -1 and start < end:

    manual_name = "tarpitd.py.1"
    # 生成一个新的内容，可以根据需要修改
    new_content = open(f"./misc/{manual_name}.md","r").read()
    lines = new_content.splitlines()
    new_content = ""
    # 遍历每一行
    for line in lines:
        # 如果这一行以 “\” 结尾，就把它替换为 “\\”
        if line.endswith("\\"):
            line = line.replace("\\", "\\\\")
        new_content += line +  "\n"
        # if len(line) < 70 :
        #     line = line + " " * (74 - len(line)) 
        # new_content += '\"' + line + ' \\n\"' + "\n"

    # 用新的内容替换原来的内容
    content = content[:start] + f"\n_MANUAL_{manual_name.upper().replace(".","_")}=\"\"\"\n" + new_content + "\n"+ "\"\"\"" +"\n" +content[end:]
    print(content)
    file.close()

    with open("./src/tarpitd.py","w") as f:
    # 写入新的内容
        f.write(content)
    
    # 打印成功信息
    print("File updated successfully")
else:
    # 打印错误信息
    print("Could not find two MARK_HERE tags in the file")