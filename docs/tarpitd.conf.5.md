## NAME

tarpitd.conf - configuration file of tarpitd

## DESCRIPTION

It is a TOML format file.

## `[tarpits.<name>]` Table

#### `<name>`

Name of this tarpit.

For reference in log output. Has no effect on behavior.

#### `pattern=` (str)

Specifies the tarpit pattern.

The name of the pattern is case-insensitive. For a complete list of supported patterns, see [tarpit.py(1)](./tarpitd.py.1.md).

#### `rate_limit=` (int)

Sets the data transfer rate limit.

Follows the same rule as [tarpit.py(1)](./tarpitd.py.1.md).

#### `bind=` (table)

A list of addresses and ports to listen on.

Every item in this list should contain `host` and `port` values; see the example below.

#### `max_clients=` (int)

The maximum number of clients the server will handle. This is calculated per bind port.

#### `client_examine` (bool)

Examine the client before sending a response.

## `[client_trace]` Table

#### `enable=` (bool)

Enable logging of client access.

#### `stdout=` (bool)

Output the client trace log to stdout (if client_trace is enabled).

Note: Normal runtime logs are printed to stderr. This behavior is hard-coded. Please use a service manager or shell redirection if you want to save the log file.

#### `file=` (str)

Path to the client_trace log file.

## Example

```toml
[tarpits]
[tarpits.my_cool_ssh_tarpit]
pattern = "ssh_trans_hold"
client_examine = true
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
