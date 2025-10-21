# Tarpitd.py

[English](./README.md) | [文档](https://imbearchild.github.io/tarpitd.py)

Tarpitd.py 是一个守护进程，实现了多种响应模式来模拟常见的网络服务，旨在通过拖慢或导致崩溃来干扰客户端活动。

这个轻量级的单文件 Python 程序专为低资源消耗而构建。其主要目标是通过故意减慢恶意或行为不当的客户端的交互来阻止它们。

## 快速开始

**注意：** Tarpitd.py 需要 Python 3.11 或更高版本！

只需下载脚本并运行：

```bash
wget --output-document tarpitd.py \
https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py

python ./tarpitd.py -s ssh_trans_hold:0.0.0.0:2222
```

上述命令会在你的主机上启动一个 SSH "焦油坑"，监听在 2222 端口上。
尝试用你的 SSH 客户端连接它，看看它如何被卡住。

## 安装

你无需运行 `pip install` 或克隆任何仓库——只需下载 [tarpitd.py](https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py) 脚本并放置在你喜欢的任何位置。

要将其作为可执行文件使用，请将脚本移动到 `$PATH` 中列出的目录（通常是 `/usr/local/bin` 或 `~/.local/bin`）并将其标记为可执行：

```bash
chmod +x tarpitd.py
```

如果你更愿意通过 pip 安装，可以使用：

```bash
python -m pip install git+https://github.com/ImBearChild/tarpitd.py.git@main
```

## 文档

详细的使用信息请参考我们的[在线文档](https://imbearchild.github.io/tarpitd.py)和手册页（[tarpitd.py.1](docs/tarpitd.py.1.md)、[tarpitd.conf.5](docs/tarpitd.conf.5.md)）

如果你已经下载了脚本，也可以通过执行以下命令查看内置手册：

```bash
python tarpitd.py --manual
```

或者，在任何文本编辑器中打开脚本直接查看嵌入的手册文本。

---

## 开发和贡献

Tarpitd.py 设计为易于修改——只需编辑单个脚本文件。欢迎贡献。

要运行测试，请执行：

```bash
python -m unittest discover -vb -s ./src
```

在进行更改后更新嵌入的文档：

```bash
python misc/insert_doc.py
```

为了更好的体验，你可以使用 [hatch](https://hatch.pypa.io/)：

```bash
hatch run tarpitd.py # 在开发环境中运行
hatch test # 运行 pytest 而不是普通的 unittest
hatch run docs:serve 
```