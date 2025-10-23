set -o errexit
set -o nounset
set -o noglob
set -o pipefail

secondary_ip=$(jq -r '.info."szh-secondary".ipv4[0]' < /mp/devel/.generated/multipass_info.json)
tertiary_ip=$(jq -r '.info."szh-tertiary".ipv4[0]' < /mp/devel/.generated/multipass_info.json)

install --owner=root --group=root --mode=0755 --directory /etc/bind/zones

install --owner=root --group=root --mode=0644 --no-target-directory /mp/devel/example-zone /etc/bind/zones/example.com.zone
install --owner=root --group=root --mode=0644 --no-target-directory /mp/devel/example-zone /etc/bind/zones/example.net.zone
install --owner=root --group=root --mode=0644 --no-target-directory /mp/devel/example-zone /etc/bind/zones/example.org.zone

sed -e "s/__SECONDARY_IP__/${secondary_ip}/" \
    -e "s/__TERTIARY_IP__/${tertiary_ip}/" \
    < /mp/devel/named.conf.primary.in \
    | install --owner=root --group=root --mode=0644 --no-target-directory \
              /dev/stdin /etc/bind/named.conf.local

install --owner=root --group=root --mode=0644 /mp/devel/named.conf.options /etc/bind/

systemctl restart named.service
