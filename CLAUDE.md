# CLAUDE.md

This repository is public. Everything you write here goes to the internet, and a `git push` cannot be taken back: the only repair is a history rewrite plus a force-push.

## Never commit personal or sensitive data

Do not write any of these into a file, a commit message, or a command example. This rule has no exception, and it applies to the archived docs in `docs/fedora/` as much as to the current ones.

- Real names, email addresses, usernames, GitHub handles, or any account identifier.
- Absolute paths that contain a home directory, for example `/home/<name>/...` or `/Users/<name>/...`.
- Hostnames, machine names, tailnet node names, or Wi-Fi SSIDs.
- NetworkManager connection names, IP addresses, subnets, or MAC addresses.
- Disk, partition, filesystem, or LUKS UUIDs.
- SSH keys of either kind, API tokens, passwords, licence keys, and hardware serial numbers.
- Links to private repositories, and commit hashes from them.

## Write a placeholder instead

| Instead of | Write |
|---|---|
| a Linux username | `<user>` |
| a personal email address | `you@example.com` |
| a GitHub noreply address | `<id>+<github-user>@users.noreply.github.com` |
| a full name in a `git config` example | `"Your Name"` |
| a NetworkManager connection name | `"<connection>"`, and tell the reader that `nmcli connection show` gives the real one |
| a home directory in a path | `~/`, or `/home/<user>/` when the file format does not expand `~` |

## What is safe to write

Hardware that identifies the model and not the machine: PCI IDs such as `14e4:43ba`, the model name `MacBookPro11,5`, driver names, package names and versions, kernel arguments, and measured values. Command output is safe only after you remove every item in the list above from it.

## Check before each commit

Run both commands and read every hit. Most hits are correct: a URL, a placeholder, a systemd unit name, or a word inside a negation ("there is no `grubby`"). A hit is a defect when it is an address, a path, or an identifier that belongs to a person or to 1 machine.

```
grep -rniE '[a-z0-9._%+-]+@[a-z0-9.-]+\.(com|org|net|io|me|dev|sh)\b|/home/[a-z]+/|/Users/[a-z]+/|([0-9a-f]{8}-[0-9a-f]{4}-){2}' --exclude-dir=.git . | grep -viE 'https?://'
grep -rnwE 'dnf|rpm|grubby|gsettings|restorecon|yum|tuned' README.md docs/*.md files/
```

The first command finds email addresses, home directories and UUIDs. On a clean tree it gives 5 hits: 3 in `docs/git-github.md` (the 2 placeholder addresses and `git@github.com`) and 2 in this file, from the lines that name them.

The second command guards a different rule: `docs/` and `files/` describe Omarchy, which is Arch. Fedora and GNOME commands belong in `docs/fedora/` only. On a clean tree it gives 4 hits, and each one is a negation: 3 say that `grubby` does not exist here, and 1 says that the Fedora procedure needed `restorecon`.

## If data leaks anyway

1. Stop. Do not push more commits on top.
2. Tell the user, and name the exact file, line, and value.
3. Wait for the user to choose the repair. An amend is enough before a push. After a push, the repair is a history rewrite and a force-push, and the user makes that decision.
