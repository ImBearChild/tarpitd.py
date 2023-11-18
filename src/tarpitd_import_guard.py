__version__ = "0.1.0"

def main_cli():
    import sys
    sys.path.pop(0)
    import re
    from tarpitd import main_cli as cli
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(cli())
