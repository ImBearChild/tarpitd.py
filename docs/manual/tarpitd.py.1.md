## NAME

tarpitd.py - making a port into tarpit

## SYNOPSIS

    tarpitd.py [-h] [-r RATE] [-c [FILE]]
        [-s PATTERN:HOST:PORT [PATTERN:HOST:PORT ...]] [--manual]

## DESCRIPTION

tarpitd.py listens on specified network ports and purposefully delays or troubles clients that connect to it. This tool can be used to tie up network connections by delivering slow or malformed responses, potentially keeping client connections open for extended periods.

## OPTIONS

#### `-c, --config FILE`

Load configuration from file.

#### `-s, --serve PATTERN:HOST:PORT [PATTERN:HOST:PORT ...]`

Start a tarpit pattern on the specified host and port.

The name of PATTERN is case-insensitive. For a complete list of supported patterns, see the “TARPIT PATTERN” section below.

#### `-r RATE, --rate-limit RATE`

Set data transfer rate limit. Tarpits pattern has their own defalut value.

A positive value limits the transfer speed to RATE *bytes* per second. 
A negative value causes the program to send one byte every |RATE| seconds (effectively 1/|RATE| *bytes* per second).

#### `-t, --trace-client [FILE]`

Log client access to FILE. Disabled by default.

The output is in jsonl format. Logs to stdout if FILE is left blank.

#### `-e, --validate-client [{check, none}]`

Examine the client before sending a response. Enabled by default. Use `-e none` to disable it.

The current implementation checks the first few bytes of the request to confirm that the client is using the corresponding protocol. 

#### `--manual MANUAL`

Display the built-in manual page. By default, tarpitd.py will open `tarpitd.py.1`.

Available manual pages include:

* tarpitd.py.1 : Program usage  
* tarpitd.conf.5 : Configuration file format

## TARPIT PATTERN

### HTTP

#### http_endless_header

Tested with: Firefox, Chromium, curl

Sends an endless stream of HTTP header lines (specifically, `Set-Cookie:`). Some clients will wait indefinitely for the header to end (or for a blank line indicating the end of the headers), while others (like curl) may have header size restrictions and close the connection once the limit is reached.

#### http_bad_site

Tested with: Firefox, Chromium

Responds to the client with a small HTML page containing many links and a dead-loop script. Browsers that support JavaScript will get stuck, and those links may cause crawlers to repeatedly pull the webpage.

#### http_deflate_html_bomb

Tested with: Firefox, Chromium

Sends a badly formed HTML document compressed using the deflate (zlib) algorithm. Most clients will consume significant CPU resources attempting to parse the malformed HTML.

Note: The response is always compressed with deflate regardless of client support, as serving uncompressed output might waste bandwidth. When using curl, use the `--compressed` option to trigger decompression and ensure you have sufficient disk space to handle the decompressed content.

#### http_deflate_size_bomb

Tested with: Firefox, Chromium, curl

Feeds the client a large amount of compressed zero data. The current implementation sends a compressed 1 MB file that decompresses to approximately 1 GB, with added invalid HTML to further confuse the client.

Note: The deflate compression algorithm has its maximum compression rate limit at 1030.3:1.

### SSH

#### endlessh

Tested with: OpenSSH

endlessh is a well-known SSH tarpit that traps SSH clients by sending endless banner messages. Although named “endlessh”, it does not implement the full SSH protocol; it simply emits continuous banner data. As a result, port scanners (such as nmap and censys) will not mark the port as running a true SSH service. tarpitd.py have this problem fixed by examining the client and sending SSH identifier to scanners.

#### ssh_trans_hold

Tested with: OpenSSH

This tarpit mimics an SSH server's initial handshake by sending valid SSH transport messages and key exchange information (per IETF RFC 4253). However, instead of completing the exchange, it repeatedly sends `SSH_MSG_IGNORE` messages. Although clients are supposed to ignore these messages according to the standard, the continual stream keeps the connection open indefinitely.

Note: The implementation advertises itself as OpenSSH 8.9 on Ubuntu and replays a pre-recorded SSH key exchange. Future updates may alter aspects of this behavior.

### TLS

#### tls_slow_hello

Tested with: openssl (cli), gnutls (cli)

Responds with a long (but still valid) server hello. Clients will read the complete message before the connection is closed.

#### tls_endless_hello_request

Tested with: openssl (cli), curl (with openssl)

Sends an endless series of HelloRequest messages to the client. According to IETF RFC 5246 (the TLS 1.2 specification), clients should ignore extra HelloRequest messages during the negotiation phase, effectively keeping the connection open. This will affect all clients using OpenSSL, including curl.

Firefox will report a timeout after 10 seconds. GNU TLS (and wget using it) will disconnect immediately, complaining about handshake failure.

### MISC

#### egsh_aminoas

Tested with: OpenSSH

An alternative to endlessh, this service not only keeps connections open but also adds a cultural touch.

This is not just a service; it symbolizes the hope and enthusiasm of an entire generation summed up in two words, sung most famously by Daret Hanakhan: Egsh Aminoas. When clients connect, they will randomly receive a quote from classical Aminoas culture, and tarpitd.py will log the same quote simultaneously.

## EXAMPLES

Print this manual:

    tarpitd.py --manual

Start an endlessh tarpit:

    tarpitd.py -s endlessh:0.0.0.0:2222

Start an endless HTTP tarpit with a 2-second per-byte delay:

    tarpitd.py -r-2 -s http_endless_header:0.0.0.0:8088

Start an endless HTTP tarpit with a rate limit of 1 KB/s:

    tarpitd.py -r1024 -s HTTP_DEFLATE_HTML_BOMB:0.0.0.0:8088

Start two different HTTP tarpit services concurrently  
(the name of the pattern is case-insensitive):

    tarpitd.py -s http_deflate_html_bomb:127.0.0.1:8080 \
                  http_endless_header:0.0.0.0:8088 

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

------

> This program was made on the lands of  
  the Aminoac people of the Amacinoas Nation.  
  We pay our respects to their Elders, past and present.  
  Sovereignty was never ceded.