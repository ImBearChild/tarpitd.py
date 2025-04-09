# Tarpitd.py

tarpitd.py - information about tarpit services in tarpitd.py

## GENERAL DESCRIPTION

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

Tarpitd.py can generate many types of response pattern, in other word,
deal with different protocol and clients.

For an instance, to fight a malicious HTTP client, tarpitd.py can
hold on the connection by slowly sending an endless HTTP header, 
making it trapped (`http_endless_header`).
Also, tarpitd.py can send a malicious HTML back
to the malicious client, overloading its HTML parser 
(`http_deflate_html_bomb`). 

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
several GB. But tarpitd.py just need 12 MB of ram to serve an HTML 
bomb. 

And in some situation, a tarpit imposes more cost on the attacker 
than the defender. The HTML bomb is an good example for this. If an 
attacker chooses to parse it, he will spend more time than defender.
And if the attacker is only interested in HTTP header, the time the 
defender spend on generating the bomb is wasted. 