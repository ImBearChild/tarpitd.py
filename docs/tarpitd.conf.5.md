## NAME

tarpitd.conf - configuration file of tarpitd

## DESCRIPTION

It is a toml format file.

## `[tarpits.<name>]` OBJECT

`<name>`  

* Name of this tarpit. 
  For reference in log output. Have no effect on behavior.

`pattern=`  

* Specify tarpit pattern. 
  The name of parttern is case-insensitive. For a complete list of supported patterns, see [tarpit.py(1)](./tarpitd.py.1.md).

`rate_limit=` 

* Set data transfer rate limit. 
  Follow same rule as [tarpit.py(1)](./tarpitd.py.1.md).

`bind=`  

* A list of address and port to listen on. 
  Every item in this list should contain `host` and `port` vaule.

## Example

```toml
[tarpits]
[tarpits.my_cool_ssh_tarpit]
pattern = "ssh_trans_hold"
rate_limit = -2
bind = [{ host = "127.0.0.1", port = "2222" }]

[tarpits.http_tarpit]
pattern = "http_endless_header"
rate_limit = 2
bind = [
  { host = "127.0.0.1", port = "8080" },
  { host = "::1", port = "8080" },
  { host = "127.0.0.1", port = "8888" },
]
```

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

------

> This program was made on the lands of
  the Aminoac people of the Amacinoas Nation. 
  We pay our respects to their Elders, past and present. 
  Sovereignty was never ceded.
