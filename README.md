# Tarpitd.py

[中文](./README.zh.md) | [Document](https://imbearchild.github.io/tarpitd.py)

Tarpitd.py is a daemon that contains different response pattern, designed to emulate common internet services in a way that can disrupt client activities, potentially slowing them down or causing crashes. 

This lightweight, single-file Python program is built for low resource consumption. Its primary goal is to deter malicious or misbehaving clients by intentionally decelerating their interactions.

## Quick Start

**Note:** Tarpitd.py requires Python 3.11 or higher!

To get started, simply download the script and run it:

```bash
wget --output-document tarpitd.py \
https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py

python ./tarpitd.py -s ssh_trans_hold:0.0.0.0:2222
```

The above command starts an ssh tarpit on your host, listening on port 2222. 
Try connecting it with your ssh client, and watch it get stuck.

## Installation

You don't have to run `pip install` or clone any repositories—just download the [tarpitd.py](https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py) script and place it wherever you prefer.

To use it as an executable, move the script to a directory listed in your `$PATH` (commonly `/usr/local/bin` or `~/.local/bin`) and mark it as executable:

```bash
chmod +x tarpitd.py
```

If you’d rather install it via pip, you can do so with:

```bash
python -m pip install git+https://github.com/ImBearChild/tarpitd.py.git@main
```

## Documentation

For detailed usage information, please refer to our [online document](https://imbearchild.github.io/tarpitd.py) 
and manual pages ([tarpitd.py.1](docs/tarpitd.py.1.md), [tarpitd.conf.5](docs/tarpitd.conf.5.md))

If you have downloaded the script, you can also view the built-in manual by executing:

```bash
python tarpitd.py --manual
```

Alternatively, open the script in any text editor to view the embedded manual text directly.

## Development and Contribution

Tarpitd.py is designed for easy modification—simply edit the single script file. Contributions are welcome.

To run the tests, execute:

```bash
python -m unittest discover -vb -s ./src
```

To update the embedded docs after making changes:

```bash
python misc/insert_doc.py
```

For better experience, you can use [hatch](https://hatch.pypa.io/):

```bash
hatch run tarpitd.py # Run in developemnt environment
hatch test # Run pytest instead of plain unittest
hatch run docs:serve # Serve mkdocs
```