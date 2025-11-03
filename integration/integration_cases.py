# ruff: noqa: E501

from dataclasses import dataclass, field


@dataclass
class PerDaemon:
    shared: str | None = None
    bind: str | None = None
    knot: str | None = None

    def pick(self, daemon: str) -> str:
        if self.shared is not None:
            return self.shared
        if self.bind is not None and daemon.lower() == "bind9":
            return self.bind
        if self.knot is not None and daemon.lower() == "knot":
            return self.knot
        return ""


@dataclass
class TestCase:
    name: str
    command: str
    zones: list[str]
    stdout: PerDaemon = field(default_factory=PerDaemon)
    stderr: PerDaemon = field(default_factory=PerDaemon)
    rc: int = 0


cases: list[TestCase] = [
    TestCase(
        name="the help command",
        command="help",
        zones=[],
        stdout=PerDaemon(
            "usage: command [ZONE]\n\nhelp\t\t\tDisplay this help message\nlist\t\t\tList available zones\ndump ZONE\t\tOutput full content of ZONE\nlogs ZONE1 [ZONE2]\tOutput the last five days' log entries for ZONE(s)\nretransfer ZONE\t\tTrigger a full (AXFR) retransfer of ZONE\n"
        ),
    ),
    TestCase(
        name="the list command",
        command="list",
        zones=[],
        stdout=PerDaemon("example.com\nexample.net\n"),
    ),
    TestCase(
        name="the dump command",
        command="dump",
        zones=["example.com"],
        stdout=PerDaemon(
            bind="example.com.\t\t\t\t      3600 IN SOA\tprimary.example.com. hostmaster.example.net. 26281038 14400 3600 1209600 1800\nexample.com.\t\t\t\t      3600 IN NS\tprimary.example.com.\nexample.com.\t\t\t\t      3600 IN NS\tsecondary.example.com.\nprimary.example.com.\t\t\t      3600 IN A\t\t127.0.0.7\nsecondary.example.com.\t\t\t      3600 IN A\t\t127.0.0.1\n",
            knot="example.com. 3600 NS primary.example.com.\nexample.com. 3600 NS secondary.example.com.\nexample.com. 3600 SOA primary.example.com. hostmaster.example.net. 26281038 14400 3600 1209600 1800\nprimary.example.com. 3600 A 127.0.0.7\nsecondary.example.com. 3600 A 127.0.0.1\n",
        ),
    ),
    TestCase(
        name="the retransfer command",
        command="retransfer",
        zones=["example.com"],
        stdout=PerDaemon('Triggering retransfer of zone "example.com"\n'),
    ),
    TestCase(
        name="picking the wrong zone",
        command="retransfer",
        zones=["example.org"],
        stderr=PerDaemon("No valid zone provided\n"),
        rc=1,
    ),
    TestCase(
        name="picking a non-existent command",
        command="bazinga",
        zones=["example.com"],
        stderr=PerDaemon('Invalid command, try "help"\n'),
        rc=1,
    ),
]
