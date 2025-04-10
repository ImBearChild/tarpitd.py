## NAME

tarpitd.conf - configuration file of tarpitd

## DESCRIPTION

It is a toml format file.

## `[tarpits.<name>]` Table

#### `<name>`

Name of this tarpit. 

For reference in log output. Have no effect on behavior.

#### `pattern=` (str)

Specify tarpit pattern. 

The name of parttern is case-insensitive. For a complete list of supported patterns, see [tarpit.py(1)](./tarpitd.py.1.md).

#### `rate_limit=` (int)

Set data transfer rate limit. 

Follow same rule as [tarpit.py(1)](./tarpitd.py.1.md).

#### `bind=` (table)

A list of address and port to listen on. 

Every item in this list should contain `host` and `port` value, see example below.

#### `max_clients=` (int)

Max clients the server will handle. It's calculated per bind port.

## `[client_trace]` Table

#### `enable=` (bool)

Enable logging client access.

#### `stdout=` (bool)

Output client trace log to stdout. (If client_trace is enabled.)

Note: normal runtime log will be print on stderr, this behavior is hard coded. Please use service manager or shell to redirect output if you want to save log file.

#### `file=` (str)

Path to client_trace log file. 

## Example

```toml
[tarpits]
[tarpits.my_cool_ssh_tarpit]
pattern = "ssh_trans_hold"
max_clients = 128 
rate_limit = -2
bind = [{ host = "127.0.0.1", port = "2222" }]

[tarpits.http_tarpit]
pattern = "http_deflate_html_bomb"
rate_limit = 4096
bind = [
  { host = "127.0.0.1", port = "8080" },
  { host = "::1", port = "8080" },
  { host = "127.0.0.1", port = "8888" },
]

[tarpits.tls_tarpit]
pattern = "tls_endless_hello_request"
rate_limit = 1
bind = [
  { host = "127.0.0.1", port = "8443" },
  { host = "127.0.0.1", port = "6697" },
]

[client_trace]
enable   = true
file = "./client_trace.log"
stdout   = true
```

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

------

> This program was made on the lands of
  the Aminoac people of the Amacinoas Nation. 
  We pay our respects to their Elders, past and present. 
  Sovereignty was never ceded.
