## NAME

tarpitd.py - information about tarpit services in tarpitd.py

## GENERAL DESCRIPTION

Note: This section is for general information. And for description
on services, please refer to SERVICES section.

### TL;DR

Tarpitd.py will listen on specified ports and trouble clients that 
connect to it.

### What is a "tarpit"

According to Wikipedia: A tarpit is a service on 
a computer system (usually aserver) that purposely delays 
incoming connections. The concept is analogous with a tar pit, in
which animals can get bogged down and slowly sink under the surface,
like in a swamp. 

Tarpitd.py will partly simulate common internet services,
for an instance, HTTP, but respond in a way that may make the 
client not work properly, slow them down or make them crash.

### Why I need a "tarpit"

This is actually a good thing in some situations.
For example, an evil ssh client may connect to port 22,and tries to 
log with weak passwords. Or evil web crawlers can collect information
from your server, providing help for cracking your server.

You can use tarpit to slow them down.

### What is a service in tarpitd.py 

A service in tarpitd.py represent a pattern of response.

For an instance, to fight a malicious HTTP client, tarpitd.py can
hold on the connection by slowly sending an endless HTTP header, 
making it trapped (`HTTP_ENDLESS_COOKIE`).
Also, tarpitd.py can send a malicious HTML back
to the malicious client, overloading its HTML parser 
(`HTTP_DEFLATE_HTML_BOMB`). 

Different responses have different consequences, and different 
clients may handle the same response 
differently. So even for one protocol, there may be more than 
one `service` in tarpitd.py correspond to it.

## SERVICES

### HTTP_ENDLESS_COOKIE

Tested with client: Firefox, Chromium, curl

Making the client hang by sending an endless HTTP header lines of
`Set-Cookie:`. Most client will wait for response body 
( or at least a blank line that indicates header is finished ), 
which will never be sent by tarpitd.py.

### HTTP_DEFLATE_HTML_BOMB

Tested with client: Firefox, Chromium

A badly formed HTML compressed by deflate (zlib) will be sent by 
tarpitd.py. It's so bad that most client will waste a lot of time
(more precisely, CPU time ) on parsing it.

Some client won't bother to prase HTML, so this may not useful
for them.

### HTTP_DEFLATE_SIZE_BOMB

Tested with client: Firefox, Chromium, curl

Feeding client with a lot of compressed zero. The current 
implementation sends a compressed 1 MB file, which is approximately 
1 GB decompressed, plus some invalid HTML code to trick client.

Curl won't decompress content by default. If you want to test this 
with curl, please add `--compressed` option to it, and make sure you
have enough space for decompressed data.

### MISC_ENDLESSH

Have been tested with client: openssh

Endlessh is a famous ssh tarpit. It keeps SSH clients locked up for
hours or even days at a time by sending endless banners. Despite its 
name, technically this is not SSH, but an endless banner sender.
Endless does implement no part of the SSH protocol, and no port 
scanner will think it is SSH ( at least nmap and censys don't mark 
this as SSH).

The current implementation in tarpitd.py is just an alias of 
MISC_EGSH_AMINOAS.

### MISC_EGSH_AMINOAS

Have been tested with client: openssh

This service can be used as an alternative to endlessh.

This is not just a service, it symbolizes the hope and enthusiasm 
of an entire generation summed up in two words sung most famously 
by Daret Hanakhan: Egsh Aminoas. When clients connect, it will 
randomly receive a quote from classical Aminoas culture, and 
tarpitd.py will show you the same quote in log at the same time.

Hope this song will bring you homesickness. And remember ... 
You are always welcome in Aminoas.
