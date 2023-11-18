## NAME

tarpitd.py - a daemon making a port into tarpit

## SYNOPSIS

    tarpitd.py [-h] [-r RATE] 
        [-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]] [--manual]

## DESCRIPTION

Tarpitd.py will listen on specified ports and trouble clients that 
connect to it. For more information on tarpitd.py, please refer to 
[tarpitd.py(7)](./tarpitd.py.7.md), or use:

    tarpitd.py --manual tarpitd.py.7

## OPTIONS

`-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]`
`--serve SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]`

Start a service on specified host and port. 
The name of service is case-insensitive.

`-r RATE, --rate RATE`

Set data transfer rate limit.
Positive value limit transfer speed to RATE *byte* per second.
Negative value will make program send one byte in RATE second.
(In other word, negative vale means 1/RATE byte per second.)

## EXAMPLES

Print this manual:

    tarpitd.py --manual

Start an endlessh tarpit:

    tarpitd.py -s misc_endlessh:0.0.0.0:2222

Start an endless HTTP tarpit on 0.0.0.0:8080, send a byte every two
seconds:

    tarpitd.py -r-2 -s HTTP_ENDLESS_COOKIE:0.0.0.0:8088

Start an endless HTTP tarpit on 0.0.0.0:8088, limit the transfer speed
to 1 KB/s:

    tarpitd.py -r1024 -s HTTP_DEFLATE_HTML_BOMB:0.0.0.0:8088

Start two different HTTP tarpit at the same time
(the name of service is case-insensitive):

    tarpitd.py -s http_deflate_html_bomb:127.0.0.1:8080 \
                  HTTP_ENDLESS_COOKIE:0.0.0.0:8088 

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]
