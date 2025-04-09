## NAME

tarpitd.py - making a port into tarpit

## SYNOPSIS

    tarpitd.py [-h] [-r RATE] [-c [FILE]]
        [-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]] [--manual]

## DESCRIPTION

Tarpitd.py will listen on specified ports and trouble clients that 
connect to it. 

## OPTIONS

#### `-c, --config FILE`

Load configuration from file.

#### `-s, --serve PATTERN:HOST:PORT [SERVICE:HOST:PORT ...]`  

Start a tarpit pattern on specified host and port. 

The name of pattern is case-insensitive. For the full list of 
supported patterns, please refer to lines below.

#### `-r RATE, --rate-limit RATE`

Set data transfer rate limit.

Positive value limit transfer speed to RATE *byte* per second.
Negative value will make program send one byte in RATE second.
(In other word, negative vale means 1/RATE byte per second.)

#### `--manual MANUAL`

Show built-in manual page. Will open `tarpitd.py.1` by default.

Available manual pages:

* tarpitd.py.1 : Program usage
* tarpitd.conf.5 : Configuration file format

## TARPIT PATTERN

### HTTP

#### http_endless_header

Tested with client: Firefox, Chromium, curl

Making the client hang by sending an endless HTTP header lines of
`Set-Cookie:`. Some client will wait for response body 
(or at least a blank line that indicates header is finished), 
which will never be sent by tarpitd.py. 
Some clients, such as curl, have limited the header size. Those clients will close connection 
when limit is reached.

#### http_deflate_html_bomb

Tested with client: Firefox, Chromium

A badly formed HTML compressed by deflate (zlib) will be sent by 
tarpitd.py. It's so bad that most client will waste a lot of time
(more precisely, CPU time) on parsing it.

Some client won't bother to parse HTML, so this may not useful
for them. Content sent by this service is always compressed with
deflate algorithm, no matter if client support it or not.
Because it's pointless to serve uncompressed garbage, which
may cause huge potential waste of bandwidth, and most
clients support deflate algorithm.

#### http_deflate_size_bomb

Tested with client: Firefox, Chromium, curl

Feeding client with a lot of compressed zero. The current 
implementation sends a compressed 1 MB file, which is approximately 
1 GB decompressed, plus some invalid HTML code to trick client.
And deflate compress algorithm has its maximum compression 
rate limit, at 1030.3:1.

Curl won't decompress content by default. If you want to test this 
with curl, please add `--compressed` option to it, and make sure you
have enough space for decompressed data.

### SSH

#### endlessh

Have been tested with client: openssh

Endlessh is a famous ssh tarpit. It keeps SSH clients locked up for
hours or even days at a time by sending endless banners. Despite its 
name, technically this is not SSH, but an endless banner sender.
Endless does implement no part of the SSH protocol, and no port 
scanner will think it is SSH (at least nmap and censys don't mark 
this as SSH).

### ssh_trans_hold

Have been tested with client: openssh

This tarpit will keep the connection open by sending valid SSH 
transport message. It follows IETF RFC 4253, which defines the SSH
protocol. 

First, it acts like a normal SSH server, sending server identification 
string, and send key exchange message about algorithm negotiation 
after it. But it won't complete the key exchange, instead, sending 
SSH_MSG_IGNORE repeatedly. The standard notes that clients MUST 
ignore those message, but keeping receiving data will keep 
connection open. So those clients will never disconnect.

The current implementation reports itself as OpenSSH 8.9 on Ubuntu 
and replays a pre-recorded OpenSSH key exchange algorithm 
negotiation request. This behavior may change in the future and 
affect the reporting results of some port scanners.

### MISC

#### egsh_aminoas

Have been tested with client: openssh

This service can be used as an alternative to endlessh.

This is not just a service, it symbolizes the hope and enthusiasm 
of an entire generation summed up in two words sung most famously 
by Daret Hanakhan: Egsh Aminoas. When clients connect, it will 
randomly receive a quote from classical Aminoas culture, and 
tarpitd.py will show you the same quote in log at the same time.

## EXAMPLES

Print this manual:

    tarpitd.py --manual

Start an endlessh tarpit:

    tarpitd.py -s endlessh:0.0.0.0:2222

Start an endless HTTP tarpit on 0.0.0.0:8080, send a byte every two
seconds:

    tarpitd.py -r-2 -s HTTP_ENDLESS_COOKIE:0.0.0.0:8088

Start an endless HTTP tarpit on 0.0.0.0:8088, limit the transfer speed
to 1 KB/s:

    tarpitd.py -r1024 -s HTTP_DEFLATE_HTML_BOMB:0.0.0.0:8088

Start two different HTTP tarpit at the same time
(the name of pattern is case-insensitive):

    tarpitd.py -s http_deflate_html_bomb:127.0.0.1:8080 \
                  HTTP_ENDLESS_COOKIE:0.0.0.0:8088 

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]

------

> This program was made on the lands of
  the Aminoac people of the Amacinoas Nation. 
  We pay our respects to their Elders, past and present. 
  Sovereignty was never ceded.
