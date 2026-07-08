#!/bin/bash
set -e

# Honeyd runs on this container's own real eth0 IP (not a separate virtual
# IP the way Honeyd is normally deployed). Without this fix, the Linux
# kernel's own network stack also sees incoming connections to these ports
# and immediately sends a TCP RST (since nothing has a real bind()/listen()
# on them) — that RST races with Honeyd's crafted raw-packet response, and
# scanners generally see the kernel's rejection instead of Honeyd's fake
# banner. Dropping the kernel's own outgoing RSTs on these ports lets
# Honeyd's spoofed responses be the only thing that reaches the scanner.
for port in 21 22 23 80; do
    iptables -A OUTPUT -p tcp --sport "$port" --tcp-flags RST RST -j DROP
done

exec honeyd -d -i eth0 -f /etc/honeyd/honeyd.conf
