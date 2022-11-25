# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"

  config.vm.define "primary" do |primary|
    primary.vm.network "private_network", ip: "192.168.63.10"
    primary.vm.hostname = "szh-primary"

    primary.vm.provision "shell", inline: <<-SHELL
      apt-get update --quiet --quiet
      DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes bind9 emacs-nox

      install --owner=root --group=root --mode=0755 --directory /etc/bind/zones
      install --owner=root --group=root --mode=0644 /vagrant/dev/example-zone /etc/bind/zones/example.com.zone
      install --owner=root --group=root --mode=0644 /vagrant/dev/example-zone /etc/bind/zones/example.net.zone
      install --owner=root --group=root --mode=0644 /vagrant/dev/example-zone /etc/bind/zones/example.org.zone
      install --owner=root --group=root --mode=0644 /vagrant/dev/named.conf.primary /etc/bind/named.conf.local
      install --owner=root --group=root --mode=0644 /vagrant/dev/named.conf.options /etc/bind/
      systemctl restart named
    SHELL
  end

  config.vm.define "secondary" do |secondary|
    secondary.vm.network "private_network", ip: "192.168.63.11"
    secondary.vm.hostname = "szh-secondary"

    secondary.vm.provision "shell", inline: <<-SHELL
      apt-get update --quiet --quiet
      DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes bind9 emacs-nox python3-venv

      install --owner=root --group=root --mode=0644 /vagrant/dev/named.conf.secondary /etc/bind/named.conf.local
      install --owner=root --group=root --mode=0644 /vagrant/dev/named.conf.options /etc/bind/

      python3 -m venv /opt/ssh-zone-handler
      /opt/ssh-zone-handler/bin/pip3 install --editable /vagrant/
      install --owner=root --group=root --mode=0644 /vagrant/zone-handler.yaml.bind.example /etc/zone-handler.yaml

      adduser --quiet --disabled-password --gecos "Alice,,,,Living Next Door" alice
      install --owner=alice --group=alice --mode=0700 --directory /home/alice/.ssh
      install --owner=alice --group=alice --mode=0644 /home/vagrant/.ssh/authorized_keys /home/alice/.ssh/

      adduser --quiet --system --no-create-home --home /nonexistent --shell /usr/sbin/nologin --ingroup systemd-journal log-viewer
      /opt/ssh-zone-handler/bin/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler

      echo -e "\nMatch User alice\n\tForceCommand /opt/ssh-zone-handler/bin/szh-wrapper\n\tPermitTTY no\n\tAllowTcpForwarding no\n\tX11Forwarding no" >> /etc/ssh/sshd_config

      systemctl restart named ssh
    SHELL
  end

  config.vm.define "tertiary" do |tertiary|
    tertiary.vm.network "private_network", ip: "192.168.63.12"
    tertiary.vm.hostname = "szh-tertiary"

    tertiary.vm.provision "shell", inline: <<-SHELL
      apt-get update --quiet --quiet
      DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes knot emacs-nox python3-venv

      install --owner=root --group=root --mode=0644 /vagrant/dev/knot.conf /etc/knot/knot.conf

      python3 -m venv /opt/ssh-zone-handler
      /opt/ssh-zone-handler/bin/pip3 install --editable /vagrant/
      install --owner=root --group=root --mode=0644 /vagrant/zone-handler.yaml.knot.example /etc/zone-handler.yaml

      adduser --quiet --disabled-password --gecos "Alice,,,,Living Next Door" alice
      install --owner=alice --group=alice --mode=0700 --directory /home/alice/.ssh
      install --owner=alice --group=alice --mode=0644 /home/vagrant/.ssh/authorized_keys /home/alice/.ssh/

      adduser --quiet --system --no-create-home --home /nonexistent --shell /usr/sbin/nologin --ingroup systemd-journal log-viewer
      /opt/ssh-zone-handler/bin/szh-sudoers | EDITOR="tee" visudo -f /etc/sudoers.d/zone-handler

      echo -e "\nMatch User alice\n\tForceCommand /opt/ssh-zone-handler/bin/szh-wrapper\n\tPermitTTY no\n\tAllowTcpForwarding no\n\tX11Forwarding no" >> /etc/ssh/sshd_config

      systemctl restart knot ssh
    SHELL
  end
end
