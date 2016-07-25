import csv

from fabric.api import *
from fabric.contrib.files import *
from fabric.utils import warn, abort, puts


REGEX_IPERF_PID_OUTPUT = 'The Iperf daemon process ID : (?P<pid>\d+)'

REGEX_IPERF_CLIENT_OUTPUT = '\[[ 0-9]+\]  [0-9.]+- *(?P<time>[0-9.]+ sec) * ' \
                            '(?P<xfer>[0-9.]+ [GMK]Bytes) *' \
                            '(?P<tput>[0-9.]+ [GMK]bits/sec)'



# TODO: push ssh key task
# TODO: sudoers task

def start_iperf_server(port=5005):
    # TODO figure out why this doesn't work consistently
    output = sudo("iperf -s -p %s -D" % port)
    try:
        pid = re.compile(REGEX_IPERF_PID_OUTPUT,
                         flags=re.MULTILINE).search(output.stdout).group('pid')
        puts("found pid %s" % pid)
    except AttributeError:
        warn("could not find pid for iperf on %(host)s" % env)


def _process_iperf_client_output(output):
    rx = re.compile(REGEX_IPERF_CLIENT_OUTPUT)
    try:
        rx_matches = rx.search(output)
        return rx_matches.groupdict()
    except AttributeError:
        return None


def run_iperf_client(server, time=30, port=5005):
    output = run("iperf -c {s} -t {t} -p {p}".format(s=server, t=time, p=port))
    results = _process_iperf_client_output(output)
    return results


def print_results(results):
    sio = StringIO()
    try:
        csvwriter = csv.writer(sio)
        csvwriter.writerow([' '] + results.keys())
        for tohost in results.keys():
            row = []
            for colheader in results.keys():
                if colheader is tohost:
                    row.append('X')
                else:
                    row.append(results[tohost][colheader]['tput'])

            csvwriter.writerow([tohost] + row)
        print sio.getvalue()
    finally:
        sio.close()


def run_iperf_between_hosts(time, port):
    """Runs an iperf test from all other hosts to this host"""
    execute(start_iperf_server, port=port, hosts=env.host)
    iperf_clients = [h for h in env.hosts if h is not env.host]
    results = execute(run_iperf_client, server=env.host, port=port,
                      time=time, hosts=iperf_clients)
    execute(killall_iperf, hosts=env.host)
    return results


@runs_once
def test_network(time=30, port=5005):
    """Tests paths between all hosts and outputs table of results

    Optional parameters:
     time: duration of iperf tests (default: 30s)
     port: change iperf port (default: 5005)
    """
    results = execute(run_iperf_between_hosts, time=time, port=port)
    print_results(results)


def install_iperf():
    if exists('/etc/redhat-release'):
        puts("Detected RedHat distro, installing iperf")
        sudo('yum install -y iperf')
    elif exists('/etc/debian_version'):
        puts("Detected Debian distro, installing iperf")
        sudo('apt-get install -y iperf')
    else:
        abort("Can't detect distro; giving up!")


def killall_iperf():
    sudo("killall -9 iperf", warn_only=True)


def runme(cmd):
    """Runs command on all hosts"""
    run(cmd)

