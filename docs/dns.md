# DNS: the HaGeZi filtering resolvers

**Status:** Applied and verified 2026-09-18. Source: the Claude Code session of
2026-09-18.

**Change:** The system resolver moves from Cloudflare, which is the Omarchy default, to
[HaGeZi DNS](https://github.com/hagezi/dns-servers). HaGeZi is a free, non-commercial
public resolver in the EU. It blocks ads, tracking, analytics, telemetry, phishing,
malware, scam, fake and cryptojacking domains at the DNS level, for every application on
the machine and not only the browser.

**Servers:** `root.hagezi.org` (Falkenstein, DE) first, `wurzn.hagezi.org` (Nuremberg,
DE) as the backup. Both are "full protection" servers, so the blocking is the same on
each one. systemd-resolved sends queries to the first server and moves to the next one
after a failure.

## Why these 2 servers

Measured from Copenhagen on 2026-09-18, 5 uncached queries per server, median:

| Server | Location | Address | Median |
|---|---|---|---|
| `root.hagezi.org` | Falkenstein, DE | `188.34.161.210` | 32.0 ms |
| `wurzn.hagezi.org` | Nuremberg, DE | `159.69.155.94` | 40.8 ms |
| `juuri.hagezi.org` | Helsinki, FI | `95.217.163.17` | 42.0 ms |
| `ctif.hagezi.org` | Nuremberg, DE | `162.55.58.40` | 56.4 ms |
| Cloudflare (the old setting) | anycast | `1.1.1.1` | 9.1 ms |

`ctif.hagezi.org` is the threat-only server. It blocks phishing and malware but no ads
or trackers. To use it instead, put `162.55.58.40` and `2a01:4f8:1c19:6c19::1` in the
step below, and `#ctif.hagezi.org` in the drop-in.

**Cost:** An uncached lookup takes about 23 ms more than Cloudflare. HaGeZi runs on
single Hetzner machines in Germany. Cloudflare runs anycast with a point of presence in
Copenhagen, so it is always nearer. systemd-resolved caches, so the penalty applies to
the first lookup of a name only.

## Why `omarchy dns Custom` is not enough on its own

`omarchy dns Custom` writes 3 places: the `[global-dns-domain-*] servers=` list in
`/etc/NetworkManager/conf.d/20-omarchy-dns.conf`, the per-connection `ipv4.dns` and
`ipv6.dns` properties, and the `DNS=` line in `/etc/systemd/resolved.conf`. It writes
the same string to NetworkManager and to systemd-resolved, but the 2 want different
syntax for a DNS-over-TLS server name:

| Consumer | Documented syntax for a server name |
|---|---|
| NetworkManager 1.58.1 | `dns+tls://ADDRESS[:PORT][#SERVERNAME]` (`man NetworkManager.conf`) |
| systemd-resolved 261 | `ADDRESS[:PORT][%ifname][#SNI]`, no URI prefix (`man resolved.conf`) |

No single input satisfies both. `omarchy dns Custom` also writes no `DNSOverTLS=` line,
so DNS over TLS turns off, while the Cloudflare and Google settings turn it on.

**Fix:** Give `omarchy dns Custom` plain IP addresses, which both consumers accept, then
override the resolver half with a drop-in. systemd reads
`/etc/systemd/resolved.conf.d/*.conf` after `resolved.conf`, so the drop-in wins.
Confirm the order with `systemd-analyze cat-config systemd/resolved.conf`.

## Apply

> **Caution:** `/etc/systemd/resolved.conf.d/30-hagezi-dot.conf` also overrides a later
> `omarchy dns Cloudflare`, `omarchy dns Google` or `omarchy dns DHCP`. The `omarchy dns`
> command reports the new provider, but name resolution stays on HaGeZi. Delete the file
> before you change the provider.

1. Install the drop-in. Do this before step 2, because `omarchy-dns` reloads
   NetworkManager and systemd-resolved at the end, and 1 reload then applies both:
   ```
   sudo install -m 0644 -o root -g root files/etc/systemd/resolved.conf.d/30-hagezi-dot.conf /etc/systemd/resolved.conf.d/30-hagezi-dot.conf
   ```
2. Set the addresses. `omarchy-dns` reads them from standard input:
   ```
   echo "188.34.161.210 2a01:4f8:c17:1c66::1 159.69.155.94 2a01:4f8:1c1c:d363::1" | sudo omarchy-dns Custom
   ```
3. Empty the resolver cache:
   ```
   resolvectl flush-caches
   ```

## Verify

```
resolvectl status | head -12
```

`DNS Servers` shows `188.34.161.210#root.hagezi.org` and the other 3. `Protocols` shows
`DNSOverTLS=opportunistic`.

```
resolvectl query google-analytics.com    # 0.0.0.0, the block answer
resolvectl query github.com              # a real address
omarchy dns                              # Custom
```

To see the encrypted transport in use, run a query for a new name and then:

```
ss -tnp | grep :853
```

## The 2 scopes, and why the drop-in alone does not decide the transport

`omarchy-dns` writes the addresses in 2 places, and systemd-resolved keeps them in 2
different scopes:

| Scope | Source | Servers after this change |
|---|---|---|
| Global | `/etc/systemd/resolved.conf` and the drop-in | `188.34.161.210#root.hagezi.org` and the other 3 |
| Link `wlp4s0` | NetworkManager, from `ipv4.dns` and `ipv6.dns` on the connection | `188.34.161.210` and `159.69.155.94`, with no name |

The link scope has `+DefaultRoute`, so queries go through it. `resolvectl query` confirms
this: each answer ends with `-- link: wlp4s0`. The per-link servers carry no name after
`#`, because `split_dns_servers` in `omarchy-dns` removes it before it calls
`nmcli connection modify`.

This costs nothing while `DNSOverTLS=opportunistic` is set, because that mode
authenticates no server at all. Both scopes point at the same 2 HaGeZi machines, so the
filtering is the same. Port 853 is in use: `ss -tn | grep :853` showed 2 established
connections to `188.34.161.210:853`, and `resolvectl query github.com` reported
`Data was acquired via local or encrypted transport: yes`.

### `DNSOverTLS=yes` can need one more step

> **Caution:** Do not set `DNSOverTLS=yes` and walk away. Test it first. Nobody tested
> it on this machine as of 2026-09-18, and the 2 scopes above make the result hard to
> predict.

`man resolved.conf` gives the validation rule: with a name after `#`, systemd-resolved
validates the certificate against that name. Without a name, it validates against the IP
address of the server. The HaGeZi certificate has 1 subject alternative name,
`DNS:root.hagezi.org`, and carries no IP address. The per-link servers have no name, so
the link scope is expected to fail validation.

What that does to a query is not certain. The same page says requests go to the global
servers "in parallel to suitable per-link DNS servers". The global scope does carry the
names, so it can answer while the link scope fails. That gives a slower lookup and
errors in the journal, not a dead resolver. The opposite result, where the failing link
scope takes the query down with it, is also possible. Measure it, do not assume it.

**The test.** Every step reverts, and the whole test takes about 20 s:

1. Turn it on:
   ```
   sudo sed -i 's/^DNSOverTLS=opportunistic/DNSOverTLS=yes/' /etc/systemd/resolved.conf.d/30-hagezi-dot.conf
   sudo systemctl reload systemd-resolved && resolvectl flush-caches
   ```
2. Look at the result:
   ```
   resolvectl query github.com
   journalctl -b -u systemd-resolved --since '-2min' --no-pager | tail -20
   ```
3. Turn it off again:
   ```
   sudo sed -i 's/^DNSOverTLS=yes/DNSOverTLS=opportunistic/' /etc/systemd/resolved.conf.d/30-hagezi-dot.conf
   sudo systemctl reload systemd-resolved && resolvectl flush-caches
   ```

**If step 2 gives no address**, the link scope is the cause. Empty the per-connection DNS
to leave only the global scope and its names. `nmcli connection show` gives the
connection name:

```
sudo nmcli connection modify "<connection>" ipv4.dns "" ipv6.dns "" ipv4.ignore-auto-dns yes ipv6.ignore-auto-dns yes
```

`resolvectl status` must then show no `DNS Servers` line under `Link 2`. A later
`omarchy dns` command writes the per-connection addresses again and undoes this, so
repeat the command after each one.

Record the outcome here either way.

## Notes

- **Block answer:** A blocked name resolves to `0.0.0.0` with a TTL of 3600 s, not to
  `NXDOMAIN` or `127.0.0.1`. Connections fail at once instead of waiting for a timeout.
- **Tested on 2026-09-18 against `root.hagezi.org`:** `google-analytics.com`,
  `telemetry.mozilla.org`, `googleads.g.doubleclick.net` and `stats.g.doubleclick.net`
  all answer `0.0.0.0`. The bare name `doubleclick.net` still resolves, and so do
  `github.com` and `graph.facebook.com`.
- **Firefox:** HaGeZi answers the Firefox canary domain with `NXDOMAIN`. Firefox then
  does not turn its own DNS over HTTPS on by itself, so its queries keep going to
  HaGeZi. A DNS over HTTPS setting that you select in Firefox yourself still wins.
- **`opportunistic` does not authenticate the server.** `man resolved.conf` is explicit:
  in this mode the resolver cannot authenticate the server, and an attacker can force a
  downgrade to plain UDP. The old Cloudflare setting had the same weakness, so this is
  not a regression. To make the setting stronger, read "`DNSOverTLS=yes` can need one
  more step" above. Do not change the value on its own.
- **The certificate is valid.** On 2026-09-18 a TLS 1.3 handshake to
  `188.34.161.210:853` returned a Let's Encrypt certificate. Its only subject
  alternative name is `DNS:root.hagezi.org`. There is no IP address in it.
- **DNSSEC stays off.** `resolvectl status` reports `DNSSEC=no/unsupported`. HaGeZi
  validates DNSSEC upstream. Local validation would reject the synthetic `0.0.0.0`
  answers for blocked names.
- **Docker is not affected.** `/etc/systemd/resolved.conf.d/20-docker-dns.conf` adds a
  stub listener on `172.17.0.1`. Containers reach the same resolver and get the same
  filtering.
- **`FallbackDNS=` is dead configuration here.** `omarchy-dns` writes Quad9 into it, but
  `man resolved.conf` uses `FallbackDNS=` only when no other DNS server is known, and
  `DNS=` is set. An outage of both HaGeZi servers does not fall through to Quad9.
- **Privacy:** HaGeZi is one private operator in Germany, not a company. It states that
  it keeps no per-client query logs, sends no EDNS client subnet, and enforces QNAME
  minimisation. See [PRIVACY.md](https://github.com/hagezi/dns-servers/blob/main/PRIVACY.md).
  This trades a large operator for a small one; judge it on that basis.

## Revert

```
sudo rm /etc/systemd/resolved.conf.d/30-hagezi-dot.conf
sudo omarchy-dns Cloudflare
resolvectl flush-caches
```
