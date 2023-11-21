## NAME

tarpitd.py - information about tarpit services in tarpitd.py

## GENERAL DESCRIPTION

Note: This section is for general information. And for description
on available tarpits, please refer to TARPITS section.

### TL;DR

Tarpitd.py will listen on specified ports and trouble clients that 
connect to it.

### What is a "tarpit"

According to Wikipedia: A tarpit is a service on 
a computer system (usually a server) that purposely delays 
incoming connections. The concept is analogous with a tar pit, in
which animals can get bogged down and slowly sink under the surface,
like in a swamp. 

Tarpitd.py will partly simulate common internet services,
for an instance, HTTP, but respond in a way that may make the 
client not work properly, slow them down or make them crash.

### Why I need a "tarpit"

This is actually a good thing in some situations.
For example, an evil ssh client may connect to port 22, and tries to 
log with weak passwords. Or evil web crawlers can collect information
from your server, providing help for cracking your server.

You can use tarpit to slow them down.

### What is a service in tarpitd.py 

A tarpit in tarpitd.py represent a pattern of response.

For an instance, to fight a malicious HTTP client, tarpitd.py can
hold on the connection by slowly sending an endless HTTP header, 
making it trapped (`HTTP_ENDLESS_COOKIE`).
Also, tarpitd.py can send a malicious HTML back
to the malicious client, overloading its HTML parser 
(`HTTP_DEFLATE_HTML_BOMB`). 

Different responses have different consequences, and different 
clients may handle the same response differently. So even for one 
protocol, there may be more than one "tarpit" in tarpitd.py 
correspond to it.

### Resource consumption

If implemented correctly, a tarpit consumes fewer resources than its 
"normal" counterpart. Usually, a real server program will process 
request from client and return response to it. But a tarpit don't 
need to implement these parts.

For example, a real HTTP server will parse HTTP request and call CGI 
(Python, PHP...) to generate a valid response. But tarpitd.py will 
directly send a pre-generated content or several random bytes.

The reality is that when searching online for "how much memory does 
Apache HTTPd require at least", most answers are hundreds of MB or 
several GB. But tarpitd.py just need 2.5 MB of ram to serve an HTML 
bomb, and 4/5 of memory is used by the bomb itself. 

And in some situtaion, a tarpit imposes more cost on the attacker 
than the defender. The HTML bomb is an good exmaple for this. If an 
attacker chooses to parse it, he will spend more time than defender.
And if the attacker is only interested in HTTP header, the time the 
defender spend on generating the bomb is wasted. 

## TARPITS

### HTTP

#### http_endless_header

Tested with client: Firefox, Chromium, curl

Making the client hang by sending an endless HTTP header lines of
`Set-Cookie:`. Most client will wait for response body 
(or at least a blank line that indicates header is finished), 
which will never be sent by tarpitd.py. 

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
transport message. It follows IETF RFC 4253 (The Secure Shell (SSH) 
Transport Layer Protocol). 

First, it acts like a normal SSH server, sending identification 
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

------

> This program was made on the lands of
  the Aminoac people of the Amacinoas Nation. 
  We pay our respects to their Elders, past and present. 
  Sovereignty was never ceded.