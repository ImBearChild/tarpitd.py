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
- In contrast, tarpitd.py may require as little as 12 MB of RAM to serve something as resource-intensive as an HTML bomb.
With this bomb pre-generated, the only thing needs to do is sending the response. (Sadly, it's still larger than OpenSSHd. Python will take serval MBs, even for printing a "hello world")

In many cases, a tarpit not only conserves resources on the defending side but also imposes greater computational and time costs on the attacker. For example, if the attacker attempts to parse the malicious HTML bomb, they may expend significantly more time and resources than the defender did to generate it. Likewise, if an attacker is solely interested in receiving HTTP headers, the defender’s effort to generate a tarpit response may effectively waste the attacker’s time.

## Is it secure?

Almost yes. tarpitd.py will not read from client, so there is nothing to crack, except a few bytes to make sure the client is running corresponding protocol. Because send an HTTP response to SSH client is pointless. This feature can be turned off as desired.

## Why not use original endlessh?

Because the author of endlessh said:

> Parting exercise for the reader: Using the examples above as a starting point, implement an SMTP tarpit using asyncio. Bonus points for using TLS connections and testing it against real spammers.

So this is what I make for exercise.