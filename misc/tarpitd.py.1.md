## NAME

tarpitd.py - a daemon making a port into tarpit

## SYNOPSIS

    tarpitd.py [-h] [-v] [-r RATE] 
        [-s SERVICE:HOST:PORT [SERVICE:HOST:PORT ...]] [--manual]

## DESCRIPTION

Tarpitd.py will listen on specified ports and trouble clients that 
connect to it. For more information on tarpitd.py, please refer to 
[tarpitd.py(7)](./tarpitd.py.7.md), or use:

    tarpitd.py --manual tarpitd.py.7

## EXAMPLES

Print this manual:

    tarpitd.py --manual

Start an endless HTTP tarpit on 0.0.0.0:8080, send a byte every two
seconds:

    tarpitd.py -r-2 -s HTTP_ENDLESS_COOKIE:0.0.0.0:8088

Start two different HTTP tarpit at the same time:

    tarpitd.py -s http_deflate_bomb:0.0.0.0:8080 \
                  HTTP_ENDLESS_COOKIE:0.0.0.0:8088 

## AUTHOR

Nianqing Yao [imbearchild at outlook.com]
