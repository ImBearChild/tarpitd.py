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

#### `client_validation=` (bool)

Validate the client before sending a response. 

#### `client_trace=` (bool)

Enable logging of client access. Client validation result is logged with access log.

## `[logging]` Table

#### `main=` (str)

Path to the main log file. Special value `<stdout>` and `<stderr>` is supported.

Default is `<stderr>`.

#### `level=` (str)

Log level. 

Accept: `debug`, `info`, `warning`, `error`, `critical`. Default is `warning`.

#### `client_trace=` (str)

Path to the client_trace log file. Special value `<stdout>` and `<stderr>` is supported.

Default is `<stdout>`.


## Example

  [tarpits]
  [tarpits.my_cool_ssh_tarpit]
  pattern = "ssh_trans_hold"
  client_trace = true
  client_validation = true
  max_clients = 8152
  rate_limit = -2
  bind = [{ host = "127.0.0.1", port = "2222" }]

  [tarpits.http_tarpit]
  pattern = "http_endless_header"
  bind = [
    { host = "127.0.0.1", port = "8080" },
    { host = "::1", port = "8888" },
  ]

  [tarpits.tls_tarpit]
  pattern = "tls_slow_hello"
  rate_limit = 1
  bind = [
    { host = "127.0.0.1", port = "8443" },
  ]

  [logging]
  client_trace = "./client_trace.log"

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

------

> This program was made on the lands of
  the Aminoac people of the Amacinoas Nation. 
  We pay our respects to their Elders, past and present. 
  Sovereignty was never ceded.
