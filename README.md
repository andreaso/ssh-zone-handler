# SSH Zone Handler

* You run your own DNS server(s), providing Secondary DNS to others?
* You want to provide your DNS tenants with a bit of self-service?
* You like ssh, but you don't want to grant others full shell access?

If so, then this might just be the tool for you.


## Usage

Usage example, based on local [Vagrantfile](Vagrantfile) setup.

```
$ vagrant up
```

```
$ alias ssh="ssh -i .vagrant/machines/secondary/virtualbox/private_key"
```

```
$ ssh alice@192.168.63.11 help
usage: command [ZONE]

help                 Display this help message
list                 List available zones
dump ZONE            Output full content of ZONE
logs [ZONE1 ZONE2]   Output the last five days' log entries for ZONE(s)
retransfer ZONE      Trigger a full (AXFR) retransfer of ZONE
status ZONE          Show ZONE status
$
```

```
$ ssh alice@192.168.63.11 list
example.com
example.net
$
```

```
$ ssh alice@192.168.63.11 logs example.net
Apr 28 17:52:00 szh-secondary named[2821]: zone example.net/IN: Transfer started.
Apr 28 17:52:00 szh-secondary named[2821]: transfer of 'example.net/IN' from 192.168.63.10#53: connected using 192.168.63.10#53
Apr 28 17:52:00 szh-secondary named[2821]: zone example.net/IN: transferred serial 26281038
Apr 28 17:52:00 szh-secondary named[2821]: transfer of 'example.net/IN' from 192.168.63.10#53: Transfer status: success
Apr 28 17:52:00 szh-secondary named[2821]: transfer of 'example.net/IN' from 192.168.63.10#53: Transfer completed: 1 messages, 6 records, 190 bytes, 0.008 secs (23750 bytes/sec) (serial 26281038)
$
```


## Setup instructions

### Add sudoers user with access to journald

```
adduser --system --no-create-home --home /nonexistent --shell /usr/sbin/nologin --ingroup systemd-journal log-viewer
```


### Create configuration

Create `/etc/zone-handler.json` based on [zone-handler.json.example](zone-handler.json.example).


### Install application

```
python3 -m venv /opt/ssh-zone-handler
/opt/ssh-zone-handler/bin/pip3 install git+https://github.com/andreaso/ssh-zone-handler.git@v0.1.3
```


### Generate sudoers rules

```
/opt/ssh-zone-handler/bin/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler
```


### Configure sshd

```
Match User alice,bob
     ForceCommand /opt/ssh-zone-handler/bin/szh-wrapper
     PermitTTY no
     AllowTcpForwarding no
     X11Forwarding no
```


## Known limitations

* Currently only supports BIND
* Might be Ubuntu distro specific
* Less-than-ideal config format
