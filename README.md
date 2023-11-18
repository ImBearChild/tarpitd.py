# Tarpitd.py

Tarpitd.py will partly simulate common internet services,
for an instance, HTTP, but respond in a way that may make the 
client not work properly, slow them down or make them crash.

## Qucik start

Just download the script and run it:

```
wget --output-document tarpitd.py \
https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py

python ./tarpitd.py -s misc_endlessh:0.0.0.0:2222
```

Now an endlessh tarpit is running on your host listening port 2222.

## Install

You don't need to run `pip install` or `git clone`. Just download the script called [tarpitd.py](https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py) in this repo, and put it somewhere you see fit. 

If you want it act like an executable binary, put it inside your `$PATH` (usually `/usr/local/bin` or `~/.local/bin`), and make it executable by `chmod +x`.

In case that you still want an installation with pip:

```
pip install \
git+https://github.com/ImBearChild/tarpitd.py.git@main
```

## Document

For online usage document, please refer to [tarpitd.py(7)](./docs/tarpitd.py.7.md) and [tarpitd.py(1)](./docs/tarpitd.py.1.md).

Or you can refer to embedded manual page, if you have the script downloaded:

```
python tarpitd.py --manual tarpitd.py.7
```