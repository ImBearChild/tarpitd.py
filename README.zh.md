# Tarpitd.py

[English](./README.md)

Tarpitd.py 会模仿网络服务，拖慢连接到它的客户端，或者让这些客户端崩溃。

## Qucik start

注意：Tarpid.py 需要 Python 3.11 或者以上

只需下载然后直接运行：

```
wget --output-document tarpitd.py \
https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py

python ./tarpitd.py -s endlessh:0.0.0.0:2222
```

现在一个 endless 焦油坑在你电脑的 2222 端口上运行。

## Install

没有运行 `pip install` 或者 `git clone` 的必要。下载那个叫[tarpitd.py](https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py)的脚本然后找个你觉得合适的地方保存即可。

如果你想要让他像可执行的命令一样，你可以把它放到 `$PATH` (一般包含 `/usr/local/bin` 或者 `~/.local/bin`) 里面，然后对它 `chmod +x`。

如果你坚持使用 PIP:

```
pip install \
git+https://github.com/ImBearChild/tarpitd.py.git@main
```

## Document

在线文档在此：[tarpitd.py(7)](./docs/tarpitd.py.7.md) 和 [tarpitd.py(1)](./docs/tarpitd.py.1.md).

另外，脚本内置了手册页:

```
python tarpitd.py --manual tarpitd.py.7
```

你也可以直接用文本编辑器打开脚本查看。