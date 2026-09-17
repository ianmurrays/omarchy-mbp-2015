# Git and GitHub

> **Omarchy status, 2026-09-17: partly set up, signing is gone.** `gh` 2.101.0 is
> installed **through mise**, not pacman, and is logged in over HTTPS. But
> `~/.ssh/id_ed25519` does not exist, `~/.config/git/allowed_signers` does not exist, and
> none of `gpg.format`, `user.signingkey` or `commit.gpgsign` is set. **Commits from this
> machine are currently unsigned.** `user.email` is a personal address here, not the
> `users.noreply.github.com` address that step 6 sets.
>
> Do steps 2 to 8 again to restore signing.
>
> **Caution:** the credential helper currently points at a versioned mise path,
> `~/.local/share/mise/installs/gh/2.101.0/.../gh`. A mise upgrade of `gh` changes that
> path and breaks git authentication over HTTPS. Install `github-cli` from pacman and run
> `gh auth setup-git` again to avoid this.

## GitHub CLI and SSH commit signing

**Status:** Applied on the Fedora install 2026-09-11. A test commit gave
`Good "git" signature`. Not applied on Omarchy. Source: session `18d61c42`.

Choices: SSH signing (not GPG), the GitHub noreply email, and a key file on disk (not the
1Password SSH agent).

Replace `Your Name`, `<id>+<github-user>` and `you@example.com` with your own values.

1. Install `gh`:
   ```
   sudo pacman -S github-cli
   ```
2. Make an SSH key. The comment is a label only:
   ```
   ssh-keygen -t ed25519 -C "omarchy-mbp" -f ~/.ssh/id_ed25519
   ```
3. Log in. Select GitHub.com, SSH, upload `~/.ssh/id_ed25519.pub`, title `omarchy-mbp`,
   web browser:
   ```
   gh auth login
   ```
4. Get the scope for signing keys:
   ```
   gh auth refresh -h github.com -s admin:ssh_signing_key
   ```
5. Upload the same key as a signing key:
   ```
   gh ssh-key add ~/.ssh/id_ed25519.pub --type signing --title "omarchy-mbp"
   ```
6. Set the git config:
   ```
   git config --global user.name "Your Name"
   git config --global user.email "<id>+<github-user>@users.noreply.github.com"
   git config --global gpg.format ssh
   git config --global user.signingkey ~/.ssh/id_ed25519.pub
   git config --global commit.gpgsign true
   git config --global tag.gpgsign true
   git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
   ```
7. Make `~/.config/git/allowed_signers` with mode 0600. Put 1 line for each email:
   ```
   <id>+<github-user>@users.noreply.github.com namespaces="git" <contents of ~/.ssh/id_ed25519.pub without the comment>
   you@example.com namespaces="git" <contents of ~/.ssh/id_ed25519.pub without the comment>
   ```
8. Add GitHub to `known_hosts` and test the login:
   ```
   ssh -o StrictHostKeyChecking=accept-new -T git@github.com
   ```

**Verify:** `git log --show-signature -1` shows `Good "git" signature`. The commit on
GitHub shows "Verified".

**Notes:**

- GitHub keeps authentication keys and signing keys in 2 different lists. Without the
  `admin:ssh_signing_key` scope, the list of signing keys gives HTTP 404.
- `allowed_signers` contains only this key. Other signed commits show as not verified
  in a local `git log`. This is correct.
- `gpg --list-secret-keys` makes an empty `~/.gnupg/`. It is not used.

> **Warning:** `~/.ssh/id_ed25519` has no passphrase. Anyone who can read the file can
> sign commits and log in to GitHub as you. To add a passphrase:
> `ssh-keygen -p -f ~/.ssh/id_ed25519`.

## HTTPS for git operations

**Status:** Applied on the Fedora install 2026-09-11. Source: session `3b7a9fc1`.

1. Set the protocol:
   ```
   gh config set -h github.com git_protocol https
   ```
2. Make `gh` the git credential helper:
   ```
   gh auth setup-git -h github.com
   ```

This adds these sections to `~/.gitconfig`. The empty `helper =` line clears all earlier
helpers. The path is the `gh` that ran the command, so a pacman install gives
`/usr/bin/gh` and a mise install gives a versioned path under
`~/.local/share/mise/installs/`:

```
[credential "https://github.com"]
	helper =
	helper = !/usr/bin/gh auth git-credential
[credential "https://gist.github.com"]
	helper =
	helper = !/usr/bin/gh auth git-credential
```

**Verify:** `git ls-remote https://github.com/<user>/<repo>.git HEAD` on a private
repository answers with a SHA.

**Notes:**

- The SSH authentication key stays on GitHub. Clones from before this change keep their
  SSH remotes.
- Not applied: `git config --global url."https://github.com/".insteadOf git@github.com:`.
