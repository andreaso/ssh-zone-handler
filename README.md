# SSH Zone Handler

* You run your own DNS server(s), providing Secondary DNS to others?
* You want to provide your DNS tenants with a bit of debugging self-service?
* You like SSH, but you don't want to grant people not-you full shell access?

If so, then this might just be the tool for you.


## Usage

Usage example, based on local [Multipass][1] setup.

```
$ make vm-create
```

```
$ alias ssh='ssh -F devel/.dynamic/ssh_conf'
```

```
$ ssh zones@szh-named help
usage: command [ZONE]

help                 Display this help message
list                 List available zones
dump ZONE            Output full content of ZONE
logs ZONE1 [ZONE2]   Output the last five days' log entries for ZONE(s)
retransfer ZONE      Trigger a full (AXFR) retransfer of ZONE
$
```

```
$ ssh zones@szh-named list
example.com
example.net
$
```

```
$ ssh zones@szh-named logs example.net
Apr 28 17:52:00 szh-named named[2821]: zone example.net/IN: Transfer started.
Apr 28 17:52:00 szh-named named[2821]: transfer of 'example.net/IN' from 192.168.63.10#53: connected using 192.168.63.10#53
Apr 28 17:52:00 szh-named named[2821]: zone example.net/IN: transferred serial 26281038
Apr 28 17:52:00 szh-named named[2821]: transfer of 'example.net/IN' from 192.168.63.10#53: Transfer status: success
Apr 28 17:52:00 szh-named named[2821]: transfer of 'example.net/IN' from 192.168.63.10#53: Transfer completed: 1 messages, 6 records, 190 bytes, 0.008 secs (23750 bytes/sec) (serial 26281038)
$
```


## Setup instructions

### Create user accounts

```
adduser --comment "SSH Zone Handler journalctl sudo access" --ingroup systemd-journal --system szh-logviewer
adduser --comment "SSH Zone Handler OpenSSH AuthorizedKeysCommandUser" --system szh-sshdcmd
adduser --comment "SSH Zone Handler shared login user" --disabled-password  zones
```


### Create configuration

Create `/etc/zone-handler.yaml` based on either
[zone-handler.yaml.bind.example][2] or
[zone-handler.yaml.knot.example][3].


### Install application

```
python3 -m venv /opt/ssh-zone-handler
/opt/ssh-zone-handler/bin/pip3 install ssh-zone-handler
```


### Generate sudoers rules

```
/opt/ssh-zone-handler/bin/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler
```


### Configure sshd

```
Match User zones
     AuthorizedKeysFile none
     AuthorizedKeysCommandUser szh-sshdcmd
     AuthorizedKeysCommand /opt/ssh-zone-handler/bin/szh-sshkeys
     DisableForwarding yes
     PermitTTY no
```


## Known limitations

* Might be Debian/Ubuntu distro specific


[1]: https://documentation.ubuntu.com/multipass/
[2]: https://github.com/andreaso/ssh-zone-handler/blob/main/zone-handler.yaml.bind.example
[3]: https://github.com/andreaso/ssh-zone-handler/blob/main/zone-handler.yaml.knot.example
