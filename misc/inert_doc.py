import io

DOC_WRAP ="""# ============================================================================="""
DOC_START="""# -----------------------------------------------------------------------------"""

# 打开文件
file = open("./src/tarpitd.py","r+")

# 读取文件内容
content = file.read()

manpages = ["tarpitd.py.1","tarpitd.py.7"]
start = 0
end = 0

for manual_name in manpages:
    # 找到两个标记的位置
    start = content.index(DOC_WRAP)
    start = content.index(manual_name,start)
    start = content.index(DOC_START,start) + len(DOC_START)
    end = content.index(DOC_WRAP,start)

    print(f"{start},{end}")

    # 如果找到了两个标记，就替换它们之间的内容
    if start != -1 and end != -1 and start < end:

        # 生成一个新的内容，可以根据需要修改
        new_content = open(f"./docs/{manual_name}.md","r").read()

        # 用新的内容替换原来的内容
        content = content[:start] + f"\n_MANUAL_{manual_name.upper().replace(".","_")}=r\"\"\"\n" + new_content + "\n"+ "\"\"\"" +"\n" +content[end:]
    else:
        # 打印错误信息
        print("Could not find two MARK_HERE tags in the file")

with open("./src/tarpitd.py","w") as f:
    # 写入新的内容
    f.write(content)
    
    # 打印成功信息
print("File updated successfully")