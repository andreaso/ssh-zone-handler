set -o errexit
set -o nounset
set -o noglob
set -o pipefail

ln -s /dev/null /etc/systemd/system/named.service
ln -s /dev/null /etc/systemd/system/knot.service
apt-get install --yes bind9 knot

install --owner=root --group=root --mode=0644 --no-target-directory /mp/devel/apparmor_local_named /etc/apparmor.d/local/usr.sbin.named
apparmor_parser -r /etc/apparmor.d/usr.sbin.named

ip address add 127.0.0.7/8 dev lo
install --owner=root --group=root --mode=0644 /mp/devel/10-lo-7.network /etc/systemd/network/

adduser --no-create-home --home /var/cache/primary --group --system primary
install --owner=root --group=root --mode=0755 --directory /etc/primary /etc/primary/zones
install --owner=root --group=primary --mode=0775 --directory /var/cache/primary

install --owner=root --group=root --mode=0644 --no-target-directory /mp/devel/example-zone /etc/primary/zones/example.com.zone
install --owner=root --group=root --mode=0644 --no-target-directory /mp/devel/example-zone /etc/primary/zones/example.net.zone
install --owner=root --group=root --mode=0644 --no-target-directory /mp/devel/example-zone /etc/primary/zones/example.org.zone

install --owner=root --group=root --mode=0644 /mp/devel/primary/named.conf /mp/devel/primary/named.conf.options /mp/devel/primary/named.conf.local /etc/primary/
install --owner=root --group=root --mode=0644 /mp/devel/primary/primary.service /etc/systemd/system/

install --owner=root --group=root --mode=0644 /mp/devel/knot/knot.conf /etc/knot/

rm /etc/systemd/system/knot.service
systemctl enable --now primary.service knot.service

python3 -m venv /opt/ssh-zone-handler
/opt/ssh-zone-handler/bin/pip3 install --editable /mp/
install --owner=root --group=root --mode=0644 --no-target-directory /mp/tests/data/knot-example-config.yaml /etc/zone-handler.yaml

adduser --quiet --disabled-password --gecos "Alice,,,,Living Next Door" alice
install --owner=alice --group=alice --mode=0700 --directory /home/alice/.ssh
install --owner=alice --group=alice --mode=0644 --no-target-directory /mp/devel/.dynamic/id_alice_ed25519.pub /home/alice/.ssh/authorized_keys

adduser --quiet --system --ingroup systemd-journal log-viewer
/opt/ssh-zone-handler/bin/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler

cat /mp/devel/sshd_match >> /etc/ssh/sshd_config
systemctl restart ssh.service
