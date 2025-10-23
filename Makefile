
default: moo

moo:
	@apt moo

devel/.generated:
	mkdir devel/.generated

devel/.generated/id_alice_ed25519: devel/.generated
	ssh-keygen -q -t ed25519 -N '' -f "$@" -C alice

vm-create: devel/.generated/id_alice_ed25519
	multipass launch --name szh-primary --cloud-init ./devel/init.primary.yaml --mount $(shell pwd):/mp jammy
	multipass launch --name szh-secondary --cloud-init ./devel/init.secondary.yaml --mount $(shell pwd):/mp jammy
	multipass launch --name szh-tertiary --cloud-init ./devel/init.tertiary.yaml --mount $(shell pwd):/mp jammy
	multipass info --format=json > ./devel/.generated/multipass_info.json
	./devel/output-ssh-conf > ./devel/.generated/ssh_conf
	multipass exec szh-primary -- sudo bash /mp/devel/setup.primary.sh
	multipass exec szh-secondary -- sudo bash /mp/devel/setup.secondary.sh
	multipass exec szh-tertiary -- sudo bash /mp/devel/setup.tertiary.sh

vm-boot:
	multipass start szh-primary szh-secondary szh-tertiary

vm-shutdown:
	multipass stop szh-primary szh-secondary szh-tertiary

vm-destroy: vm-shutdown
	multipass delete --purge szh-primary szh-secondary szh-tertiary
	rm -rf ./devel/.generated

.PHONY: default moo vm-create vm-boot vm-shutdown vm-destroy
