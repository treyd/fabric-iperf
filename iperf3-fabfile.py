import csv
import sys
from fabric.api import *
from fabric.contrib.files import *
from fabric.utils import warn, abort, puts
import re

REGEX_IPERF_PID_OUTPUT = 'The Iperf daemon process ID : (?P<pid>\d+)'

#REGEX_IPERF_CLIENT_OUTPUT = '\[[ 0-9]+\]  [0-9.]+- *(?P<time>[0-9.]+ sec) * ' \
#                            '(?P<xfer>[0-9.]+ [GMK]Bytes) *' \
#                            '(?P<tput>[0-9.]+ [GMK]bits/sec)'
REGEX_IPERF_CLIENT_OUTPUT = '\[[ 0-9]+\]   [0-9.]+-*(?P<time>[0-9.]+  sec) * (?P<xfer>[0-9.]+ [GMK]Bytes) *(?P<tput>[0-9.]+ [GMK]bits/sec)'

# TODO: push ssh key task


def read_hosts(filename=None):
    """reads in a file of host strings (one per line) and sets hosts environment

    Optional parameters:
      filename: reads in host strings from file; otherwise will read STDIN
    """
    if filename:
        try:
            hostsfile = open(filename)
            env.hosts = [line.strip() for line in hostsfile.readlines()]
        except Exception as e:
            abort('problem reading hosts file %s:%s' % (filename, e))
    else:
        env.hosts = [line.strip() for line in sys.stdin.readlines()]


def start_iperf_server(port=5005):
    # TODO figure out why this doesn't work consistently
    output = run("iperf3 -s -p %s -D" % port)
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
    output = run("iperf3 -i 0 -c {s} -t {t} -p {p}".format(s=server, t=time, p=port))
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
                try:
                    row.append(results[tohost][colheader]['tput'])
                except (AttributeError, KeyError):
                    # data point doesn't exist due to self-test or failure
                    row.append('X')
                except Exception as e:
                    # something else wrong with the data point,
                    # log error and mark output
                    warn("Error parsing datapoint for dest %s from %s" % (tohost,
                                                                          colheader))
                    warn("Got exception: %s" % e)
                    row.append('Error')

            csvwriter.writerow([tohost] + row)
        print sio.getvalue()
    finally:
        sio.close()


def run_iperf_between_hosts(time, port):
    """Runs an iperf test from all other hosts to this host"""
    execute(start_iperf_server, port=port, hosts=env.host_string)
    # avoid testing to self
    iperf_clients = [h for h in env.hosts if h is not env.host_string]
    results = execute(run_iperf_client, server=env.host, port=port,
                      time=time, hosts=iperf_clients)
    execute(killall_iperf, hosts=env.host_string)
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
        run('yum install -y iperf')
    elif exists('/etc/debian_version'):
        puts("Detected Debian distro, installing iperf")
        run('apt-get install -y iperf')
    else:
        abort("Can't detect distro; giving up!")


def killall_iperf():
    run("killall -9 iperf3", warn_only=True)



