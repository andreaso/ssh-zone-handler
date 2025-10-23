set -o errexit
set -o nounset
set -o noglob
set -o pipefail

primary_ip=$(jq -r '.info."szh-primary".ipv4[0]' < /mp/devel/.generated/multipass_info.json)
tertiary_ip=$(jq -r '.info."szh-tertiary".ipv4[0]' < /mp/devel/.generated/multipass_info.json)

sed -e "s/__PRIMARY_IP__/${primary_ip}/" \
    -e "s/__TERTIARY_IP__/${tertiary_ip}/" \
    < /mp/devel/knot.conf.in \
    | install --owner=root --group=root --mode=0644 --no-target-directory \
              /dev/stdin /etc/knot/knot.conf

python3 -m venv /opt/ssh-zone-handler
/opt/ssh-zone-handler/bin/pip3 install --editable /mp/
install --owner=root --group=root --mode=0644 --no-target-directory /mp/zone-handler.yaml.knot.example /etc/zone-handler.yaml

adduser --quiet --disabled-password --gecos "Alice,,,,Living Next Door" alice
install --owner=alice --group=alice --mode=0700 --directory /home/alice/.ssh
install --owner=alice --group=alice --mode=0644 --no-target-directory /mp/devel/.generated/id_alice_ed25519.pub /home/alice/.ssh/authorized_keys

adduser --quiet --system --no-create-home --home /nonexistent --shell /usr/sbin/nologin --ingroup systemd-journal log-viewer
/opt/ssh-zone-handler/bin/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler

echo -e "\nMatch User alice\n\tForceCommand /opt/ssh-zone-handler/bin/szh-wrapper\n\tPermitTTY no\n\tAllowTcpForwarding no\n\tX11Forwarding no" >> /etc/ssh/sshd_config

systemctl restart knot.service ssh.service
