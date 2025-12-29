debian13 := https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2

default: moo

moo:
	@apt moo

devel/.dynamic:
	mkdir -m700 "$@"

vm-create: devel/.dynamic
	multipass launch --name szh-named --cloud-init ./devel/init.yaml $(debian13)
	multipass launch --name szh-knot --cloud-init ./devel/init.yaml $(debian13)
	multipass restart szh-named szh-knot
	multipass mount $(shell pwd) szh-named:/mp
	multipass mount $(shell pwd) szh-knot:/mp
	multipass info --format=json > ./devel/.dynamic/multipass_info.json
	./devel/output-ssh-conf > ./devel/.dynamic/ssh_conf
	ssh-keygen -q -t ed25519 -N '' -f "./devel/.dynamic/id_alice_ed25519" -C alice
	multipass exec szh-named -- sudo bash /mp/devel/setup.named.sh
	multipass exec szh-knot -- sudo bash /mp/devel/setup.knot.sh


vm-boot:
	multipass start szh-named szh-knot

vm-shutdown:
	multipass stop szh-named szh-knot

vm-destroy: vm-shutdown
	multipass delete --purge szh-named szh-knot
	rm -rf  ./devel/.dynamic/

.PHONY: default moo vm-create vm-boot vm-shutdown vm-destroy
