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

#### `bind=` (table)

A list of addresses and ports to listen on.

Every item in this list should contain `host` and `port` values; see the example below.

#### `rate_limit=` (int)

Sets the data transfer rate limit.

Follows the same rule as [tarpit.py(1)](./tarpitd.py.1.md).

#### `max_clients=` (int)

The maximum number of clients the server will handle. This is calculated per bind port.

#### `client_valiation=` (bool)

Validate the client before sending a response. 

#### `client_trace=` (bool)

Enable logging of client access. Client validation result is logged with access log.

## `[logging]` Table
<!--
#### `main=` (str)

Path to the main log file. Sepcial value `<stdout>` and `<stderr>` is supported.

Default is `<stderr>`.
-->
#### `client_trace=` (str)

Path to the client_trace log file. Sepcial value `<stdout>` and `<stderr>` is supported.

Default is `<stdout>`.


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
client_trace = True
bind = [
  { host = "127.0.0.1", port = "8443" },
  { host = "127.0.0.1", port = "6697" },
]

[logging]
client_trace = ./my_log.log
```

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

------

> This program was made on the lands of
  the Aminoac people of the Amacinoas Nation. 
  We pay our respects to their Elders, past and present. 
  Sovereignty was never ceded.
