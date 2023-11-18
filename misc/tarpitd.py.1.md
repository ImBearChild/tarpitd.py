## NAME

tarpitd - a daemon making a port into tarpit

## SYNOPSIS

    tarpitd.py [-h] [-v] [-c CONFIG] [-r RATE] 
        [-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]] [--manual]

## DESCRIPTION

Tarpitd.py (tarpit daemon) is a python program that set up network
tarpits. A tarpit is a service on a computer system (usually a
server) that purposely delays incoming connections.

## EXAMPLES

Print this manual:

    tarpitd.py --manual

Start an endless HTTP tarpit on 0.0.0.0:8080, send a byte every two
seconds:

    tarpitd.py -r2 -s HTTP_ENDLESS_COOKIE:0.0.0.0:8088

Start two different HTTP tarpit at the same time:

    tarpitd.py -s http_deflate_bomb:0.0.0.0:8080 \
                  HTTP_ENDLESS_COOKIE:0.0.0.0:8088 

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]
