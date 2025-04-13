# Getting Started

## Installation

**Note:** Tarpitd.py requires **Python 3.11 or higher**!

You don't have to run `pip install` or clone any repositories—just download the [tarpitd.py](https://github.com/ImBearChild/tarpitd.py/raw/main/src/tarpitd.py) script and place it wherever you prefer.

To use it as an executable, move the script to a directory listed in your `$PATH` (commonly `/usr/local/bin` or `~/.local/bin`) and mark it as executable:

```bash
chmod +x tarpitd.py
```

If you’d rather install it via pip, you can do so with:

```bash
python -m pip install git+https://github.com/ImBearChild/tarpitd.py.git@main
```

## First Few Tarpits

### Slowing Down SSH Brute-Force Attacks

SSH ports are frequent targets for brute-force attacks. By converting the SSH port into a “trap,” attackers connecting to the port receive endless banner messages or continuous ignore messages that force them to wait for a response. This significantly lengthens the time required for each attack attempt.

*Example: Run an SSH tarpit (in endlessh mode) on port 2222 of your machine:*

```bash
tarpitd.py -s endlessh:0.0.0.0:2222
```

This setup is effective for defending against SSH brute-force attacks by forcing attackers to spend much longer time on each connection, decreasing the resource they can spend on real SSH daemon.

### Thwarting Automated HTTP Scanning and Crawling

Automated tools and crawlers are often used to scan for vulnerabilities and harvest content. 

For HTTP services, you can launch a tarpit pattern that sends an endless stream of HTTP headers. This forces scanning tools and crawlers to wait, drastically reducing their efficiency. 

For clients connecting via HTTPS/TLS, you can use one of tarpitd.py’s TLS pattern – such as sending a ServerHello messages slowly. In this mode, connected TLS clients (for example, those using OpenSSL for testing or scanning) will eventually time out or declare handshake failures due to prolonged waiting.

tarpitd.py allows you to launch multiple services in a single command, each using a different pattern, listening on different addresses and ports.

*Example 1: Run both an HTTP tarpit and an TLS tarpit concurrently:*

```bash
tarpitd.py -r -2 -s HTTP_ENDLESS_COOKIE:0.0.0.0:8088 -s tls_slow_hello:127.0.0.1:8443
```

In this case, the option `-r -2` makes the program wait 2 seconds for every byte sent, forcing each malicious request to endure a long delay.

Want to fight back harder? How about sending resource-intensive deflate-compressed data? This pattern will force client consume excessive resources, making them CPU-intensive and memory-intensive.

*Example 2: Consume client resources using a deflate-compressed HTML bomb:*

```bash
tarpitd.py -r 1024 -s HTTP_DEFLATE_HTML_BOMB:0.0.0.0:8088
```

Here, the tool sends a 1 MB compressed package that, when decompressed, may consume up to 1 GB of memory, with invalid HTML can confuse the client. With a rate limit of 1 KB/s, you can control the output flow while imposing heavy resource usage on the client.

## Configuration

In a real-world scenario, you might need to defend against various types of attacks simultaneously. 

Instead of relying solely on command-line options, you can configure tarpitd.py with a dedicated configuration file. The TOML configuration file allows you to define multiple tarpit services with separate settings, such as different tarpit modes, rate limits, bind addresses, and client examination rules. This approach is particularly useful if you need to run several tarpit instances simultaneously, each with its own tailored behavior.

*Example: Combine examples up*

```toml
[tarpits]
[tarpits.my_cool_ssh_tarpit]
pattern = "ssh_trans_hold"
client_trace = true
client_valiation = true
max_clients = 8152
rate_limit = -2
bind = [{ host = "127.0.0.1", port = "2222" }]

[tarpits.http_tarpit]
pattern = "HTTP_ENDLESS_COOKIE"
bind = [
  { host = "127.0.0.1", port = "8080" },
  { host = "::1", port = "8888" },
]

[tarpits.tls_tarpit]
pattern = "tls_slow_hello"
rate_limit = 1
bind = [
  { host = "127.0.0.1", port = "8443" },
]

[logging]
client_trace = "./client_trace.log"
```

In this configuration:

* Each tarpit service (e.g., my_cool_ssh_tarpit, http_tarpit, tls_tarpit) is defined with its own settings.
* You can customize the bind addresses (host and port), rate limits, client examination, and maximum connection limits individually.
* The global [logging] section allows you to log connection details for future analysis.

Save it to `conf.toml`. And run tarpitd.py with it. 

```
tarpitd.py -c ./conf.toml
```
