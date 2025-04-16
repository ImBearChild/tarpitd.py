# About

## What Is a Tarpit?

A tarpit, as defined by Wikipedia, is a service on a computer system (typically a server) designed to intentionally delay incoming connections. This concept is analogous to an actual tar pit in nature, where animals become stuck and slowly sink beneath the surface of a swamp. Similarly, an internet tarpit slows down client connections, impeding rapid or automated access.

## Why Use a Tarpit?

A tarpit can be highly beneficial in scenarios involving hostile or automated clients. Here are some examples:

- **Brute-force Attacks:** A malicious SSH client may repeatedly attempt to log in via port 22 using weak passwords. A tarpit can slow these attempts, increasing the time cost of the attack.
- **Automated Crawlers:** Malicious web crawlers might try to gather sensitive information from your server. By deliberately slowing down their requests, a tarpit can hinder data collection and reduce the effectiveness of such attacks.

By employing a tarpit, you effectively shift the resource burden, imposing higher costs on the attacker while protecting your server's legitimate operations.

## What Is a "pattern" in tarpitd.py?

In the context of tarpitd.py, a "pattern" refers to a specific response behavior tailored to interact with different protocols and handle various types of client connections. For instance:

- **HTTP Endless Header:** To combat a malicious HTTP client, tarpitd.py might maintain a connection by slowly transmitting an endless HTTP header. This response keeps the client effectively trapped. (`http_endless_header`)
- **HTML Bomb:** Alternatively, tarpitd.py can be configured to send a malicious HTML payload that overloads the client's HTML parser, further exhausting its resources. (`http_deflate_html_bomb`)
- **SSH Transport Hold:** In order to fight against brute-force attackers, tarpitd.py will perform SSH handshake slowly, and send harmless message to keep connection open. (`ssh_trans_hold`)

Since different response patterns yield different effects—and clients may react in varied ways—tarpitd.py supports multiple tarpit strategies even for a single protocol.

## How About Resource Consumption?

An efficiently implemented tarpit is specifically designed to consume far fewer resources than a conventional server. Traditional server software processes client requests in full, including parsing requests and generating dynamic responses via CGI (e.g., Python or PHP). In contrast, tarpitd.py bypasses most of these steps, instead sending pre-generated content or even arbitrary bytes.

To put it in perspective:

- A typical HTTP server like Apache or Caddy might require hundreds of megabytes—or even gigabytes—of memory depending on the workload. And it will consume much CPU time to prepare a response.
- In contrast, tarpitd.py may require as little as 300kb of RAM to serve something as resource-intensive as an HTML bomb. With this bomb pre-generated, the only thing needs to do is sending the response. 

In many cases, a tarpit not only conserves resources on the defending side but also imposes greater computational and time costs on the attacker. For example, if the attacker attempts to parse the malicious HTML bomb, they may expend significantly more time and resources than the defender did to generate it. Likewise, if an attacker is solely interested in receiving HTTP headers, the defender’s effort to generate a tarpit response may effectively waste the attacker’s time.

## Is it secure?

Almost. tarpitd.py does not read from the client—except for a few bytes to verify that the client is using the correct protocol—so there is nothing for an attacker to crack. By default, tarpitd.py checks the client because sending an HTTP response to an SSH client is pointless, and it helps prevent null probing. This feature can be disabled if desired.

*well, technically,* in some cases tarpitd.py may read the client's request, but it does not parse it; it simply drops the data upon arrival. Reading from the client ensures that we close the TCP connection after the client, rather than before. Not all tarpit patterns include reading; for example, those employing the "endless" approach do not read.

## Why not use the original endlessh?

Because the author of endlessh stated:

> Parting exercise for the reader: Using the examples above as a starting point, implement an SMTP tarpit using asyncio. Bonus points for using TLS connections and testing it against real spammers.

Thus, this implementation was developed as an exercise.

## What is null probing?

From *[Nmap Network Scanning](https://nmap.org/book/vscan-technique.html)*:

> Once the TCP connection is made, Nmap listens for roughly five seconds. Many common services, including most FTP, SSH, SMTP, Telnet, POP3, and IMAP servers, identify themselves in an initial welcome banner. Nmap refers to this as the “NULL probe” because Nmap just listens for responses without sending any probe data.

Nmap is not the only prober that uses this technique. In some places, it is also referred to as banner grabbing. This is why the original endlessh failed to trick scanners—it sends a random string, so no probe identifies it as SSH.