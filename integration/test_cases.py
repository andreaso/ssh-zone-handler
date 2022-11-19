from dataclasses import dataclass


@dataclass
class TestCase:
    name: str
    command: str
    zones: list[str]
    stdout: str
    stderr: str = ""
    rc: int = 0


cases: list[TestCase] = [
    TestCase(
        name="help output",
        command="help",
        zones=[],
        stdout="usage: command [ZONE]\n\nhelp\t\t\tDisplay this help message\nlist\t\t\tList available zones\ndump ZONE\t\tOutput full content of ZONE\nlogs [ZONE1 ZONE2]\tOutput the last five days' log entries for ZONE(s)\nretransfer ZONE\t\tTrigger a full (AXFR) retransfer of ZONE\nstatus ZONE\t\tShow ZONE status\n",
    ),
    TestCase(
        name="listing zones",
        command="list",
        zones=[],
        stdout="example.com\nexample.net\n",
    ),
    TestCase(
        name="dummy command",
        command="bazinga",
        zones=["example.com"],
        stdout="",
        stderr='Invalid command, try "help"\n',
        rc=1,
    ),
    TestCase(
        name="triggering retransfer",
        command="retransfer",
        zones=["example.com"],
        stdout='Triggering retransfer of zone "example.com"\n',
    ),
]
