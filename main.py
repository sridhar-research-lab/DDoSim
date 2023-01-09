#!/usr/bin/env python3

import sys
import subprocess
import os
import signal
import time
import argparse
import datetime
import yaml
import random
import shutil

__author__ = 'chepeftw'

numberOfNodesStr = '20'
emulationTimeStr = '600'
scenarioSize = '300'
noBuildCacheDocker = ''
timeoutStr = '800'
networkStr = 'csma'
mode = 'single'
rootNode = '10.0.0.1'
nodeSpeed = '5'
nodePause = '1'
simulationCount = 0

numberOfNodes = 0
jobs = 1
nameList = []

baseContainerNameConn = 'myconnmanbox'
baseContainerNameDnsm = 'mydnsmasqbox'
baseContainerNameAtt = 'myattackbox'

pidsDirectory = "./var/pid/"
logsDirectory = "./var/log/"

def main():
    global numberOfNodesStr, \
        emulationTimeStr, \
        timeoutStr, \
        networkStr, \
        nodeSpeed, \
        nodePause, \
        simulationCount, \
        scenarioSize, \
        numberOfNodes, \
        nameList, \
        jobs
    #print("Main ...")

    ###############################
    # n == number of nodes
    # t == simulation time in seconds
    ###############################
    parser = argparse.ArgumentParser(description="MEDDoS Implementation.", add_help=True)
    parser.add_argument("operationStr", action="store", type=str, choices=['create', 'ns3', 'emulation', 'destroy'], help="The name of the operation to perform, options: create, ns3, emulation, destroy")

    parser.add_argument("-n", "--number", action="store",type=int, help="The number of nodes to simulate")

    parser.add_argument("-t", "--time", action="store", type=int, help="The time in seconds of NS3 simulation")

    parser.add_argument("-to", "--timeout", action="store", type=int, help="The timeout in seconds of NS3 simulation")

    parser.add_argument("-net", "--network", action="store", type=str, choices=['csma', 'wifi'], help="The type of network, options: csma, wifi")

    parser.add_argument("-s", "--size", action="store", help="The size in meters of NS3 network simulation")

    parser.add_argument("-ns", "--nodespeed", action="store", help="The speed of the nodes expressed in m/s")

    parser.add_argument("-np", "--nodepause", action="store", help="The pause of the nodes expressed in s")

    parser.add_argument("-c", "--count", action="store", help="The count of simulations")

    parser.add_argument("-j", "--jobs", action="store", type=int, help="The number of parallel jobs")

    parser.add_argument('-v', '--version', action='version', version='%(prog)s 3.0')

    #parser.print_help()
    args = parser.parse_args()

    if args.number:
        numberOfNodesStr = args.number
    if args.time:
        emulationTimeStr = args.time
    if args.timeout:
        timeoutStr = args.timeout
    if args.network:
        networkStr = args.network
    if args.size:
        scenarioSize = args.size
    if args.nodespeed:
        nodeSpeed = args.nodespeed
    if args.nodepause:
        nodePause = args.nodepause
    if args.count:
        simulationCount = int(args.count)
    if args.jobs:
        jobs = int(args.jobs)

    operation = args.operationStr

    # Display input and output file name passed as the args
    print("Number of nodes : %s" % numberOfNodesStr)
    print("Emulation time : %s" % emulationTimeStr)
    print("Operation : %s" % operation)
    print("Timeout : %s" % timeoutStr)
    print("Network Type : %s" % networkStr)
    print("Simulation Count : %s" % simulationCount)
    if networkStr == 'wifi':
        print("Node Speed : %s" % nodeSpeed)
        print("Node Pause : %s" % nodePause)
        print("Scenario Size : %s x %s" % (scenarioSize, scenarioSize))

    os.environ["NS3_HOME"] = "./ns3/ns-3-dev"

    numberOfNodes = int(numberOfNodesStr)

    global base_name
    base_name = "emu"

    for x in range(0, numberOfNodes):
        nameList.append(base_name + str(x + 1))

    if operation == "create":
        create()
    elif operation == "destroy":
        destroy()
    elif operation == "ns3":
        ns3()
    elif operation == "emulation":
        run_emu()
    else:
        print("Nothing to be done ...")


################################################################################
# handling ()
################################################################################
def check_return_code(rcode, message):
    if rcode == 0:
        print("\nSuccess: %s" % message)
        return

    print("\nError: %s" % message)
    print("")
    print('\x1b[6;30;41m' + 'STOP! Please investigate the previous error(s) and run the command again' + '\x1b[0m')
    destroy()  # Adding this in case something goes wrong, at least we do some cleanup
    sys.exit(2)


def check_return_code_chill(rcode, message):
    if rcode == 0:
        print("\nSuccess: %s" % message)
        return

    print("\nError: %s" % message)
    return

def nodes_in_pid_dir():
    return max([int(name.split(base_name)[1]) if (name.split(base_name)[1]) else 0 for name in os.listdir(pidsDirectory) if len(name.split(base_name)) > 1])

def verify_num_nodes():
    docker_files = 0
    if os.path.exists(pidsDirectory):
        if os.listdir(pidsDirectory):
            docker_files =  nodes_in_pid_dir()
            if docker_files != numberOfNodes:
                print('Please correct the number of nodes (-n %d) in the command'%(docker_files))
                sys.exit(2)
        else:
            print("Run the 'create' command and try again")
            sys.exit(2)
    else:
        print("Run the 'create' command and try again")
        sys.exit(2)

def write_conf(target, nodes, timeout, root, port, filename):
    config = {
        'target': target,
        'nodes': nodes,
        'timeout': int(timeout),
        'rootnode': root,
        'port': port
    }
    filename = "conf/" + filename
    with open(filename, 'w') as yaml_file:
        yaml.dump(config, yaml_file, default_flow_style=False)

#https://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid-in-python
def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def process(command, message = None, code = 2):
    #print(out.decode("utf-8"),error,process.returncode, type(out),type(error), error==b'')
    process = subprocess.Popen(command, shell=True ,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    out = process.communicate()[0].decode("utf-8").strip()

    if message is not None:
        out = message

    if code == 0:
        print('\r' + out, end="", flush=True)
    elif code == 1:
        print()
        print('\r' + out, end="", flush=True)
    return process.returncode

################################################################################
# create ()
################################################################################
def create():
    print("Creating ...")
    docker_files = 0
    if os.path.exists(pidsDirectory):
        if os.listdir(pidsDirectory):
            docker_files =  nodes_in_pid_dir()
            if (docker_files!=0):
                print("There are %d node(s) running. Run the 'destroy' command and try again"%(docker_files))
                return

    #############################
    # First we make sure we are running the latest version of our Ubuntu container

    # docker build -t myubuntu docker/myubuntu/.

    # r_code = subprocess.call("docker build -t %s docker/mybase/." % baseContainerName0, shell=True)
    # check_return_code(r_code, "Building regular container %s" % baseContainerName0)

    r_code = subprocess.call("DOCKER_BUILDKIT=1 docker build -t %s docker/nodes_conn/." % baseContainerNameConn, shell=True)
    check_return_code(r_code, "Building nodes container %s" % baseContainerNameConn)

    r_code = subprocess.call("DOCKER_BUILDKIT=1 docker build -t %s docker/nodes_dnsm/." % baseContainerNameDnsm, shell=True)
    check_return_code(r_code, "Building nodes container %s" % baseContainerNameDnsm)

    r_code = subprocess.call("DOCKER_BUILDKIT=1 docker build -t %s docker/attacker/." % baseContainerNameAtt, shell=True)
    check_return_code(r_code, "Building attacker container %s" % baseContainerNameAtt)

    r_code = subprocess.call('[ -d "$NS3_HOME" ]', shell=True)
    if r_code !=0 :
        print("Unable to find NS3 in", (os.environ['NS3_HOME']), ", make sure the 'install.sh' file was executed correctly")
    check_return_code(r_code,"Checking NS3 directory")

    if networkStr == 'wifi':
        r_code = subprocess.call("cd ns3 && bash update.sh tap-wifi-virtual-machine.cc", shell=True)
    else:
        r_code = subprocess.call("cd ns3 && bash update.sh tap-csma-virtual-machine.cc", shell=True)

    check_return_code(r_code,"Copying latest ns3 file")

    print("NS3 up to date!")
    print("Go to NS3 folder: cd %s" %(os.environ['NS3_HOME']))

    r_code = subprocess.call("cd $NS3_HOME && ./ns3 build -j {}".format(jobs), shell=True)

    if r_code !=0 :
        print("Unable to build NS3 in", (os.environ['NS3_HOME']), ", let's try to reconfigure. Then, try again~")
        r_code = subprocess.call("cd $NS3_HOME && ./ns3 clean &&./ns3 configure --build-profile=optimized --enable-sudo --disable-examples && ./ns3 build -j {}".format(jobs), shell=True)

    check_return_code(r_code,"NS3 BUILD")

    print('NS3 Build finished | Date now: %s' % datetime.datetime.now())

    #############################
    # First and a half ... we generate the configuration yaml files.

    write_conf(0, numberOfNodes, timeoutStr, 0, 10001, "conf1.yml")

    #############################
    # Second, we run the numberOfNodes of containers.
    # https://docs.docker.com/engine/reference/run/
    # They have to run as privileged (don't remember why, need to clarify but I read it in stackoverflow)
    # (Found it, it is to have access to all host devices, might be unsafe, will check later)
    # By default, Docker containers are "unprivileged" and cannot, for example,
    # run a Docker daemon inside a Docker container. This is because by default a container is not allowed to
    # access any devices, but a "privileged" container is given access to all devices.
    # -dit ... -d run as daemon, -i Keep STDIN open even if not attached, -t Allocate a pseudo-tty
    # --name the name of the container, using emuX
    # Finally the name of our own Ubuntu image.
    if not os.path.exists(logsDirectory):
        os.makedirs(logsDirectory)

    dir_path = os.path.dirname(os.path.realpath(__file__))

    # https://github.com/dperson/openvpn-client/issues/75
    acc_status = 0
    acc_status = process("docker run --restart=always --sysctl net.ipv6.conf.all.disable_ipv6=0 --privileged -dit --net=none --name %s %s" % (nameList[0], baseContainerNameAtt), None, 1)

    for x in range(1, numberOfNodes):
        '''
        if not os.path.exists(logsDirectory + nameList[x]):
            os.makedirs(logsDirectory + nameList[x])

        # "." are not allowed in the -v of docker and it just work with absolute paths
        log_host_path = dir_path + logsDirectory[1:] + nameList[x]
        conf_host_path = dir_path + "/conf"

        volumes = "-v " + log_host_path + ":/var/log/golang "
        volumes += "-v " + conf_host_path + ":/beacon_conf "

        print("VOLUMES: " + volumes)
        '''
        selected = random.choice([1, 2]) # Connman or Dnsmasq

        if selected ==1:
            acc_status += process("docker run --restart=always --sysctl net.ipv6.conf.all.disable_ipv6=0 --privileged -dit --net=none --name %s %s" % (nameList[x], baseContainerNameConn), None, 0)
        else:
            acc_status += process("docker run --restart=always --sysctl net.ipv6.conf.all.disable_ipv6=0 --privileged -dit --net=none --name %s %s" % (nameList[x], baseContainerNameDnsm), None, 0)

    # If something went wrong running the docker containers, we panic and exit
    check_return_code(acc_status, "Running docker containers")

    time.sleep(1)
    print('Finished running containers | Date now: %s' % datetime.datetime.now())

    #############################
    # Third, we create the bridges and the tap interfaces for NS3
    # Based on NS3 scripts ... https://www.nsnam.org/docs/release/3.25/doxygen/tap-wifi-virtual-machine_8cc.html
    # But in the source you can find more examples in the same dir.
    acc_status = 0
    for x in range(0, numberOfNodes):
        acc_status += process("bash net/singleSetup.sh %s" % (nameList[x]), None, 0)

    check_return_code(acc_status, "Creating bridge and tap interface")

    acc_status += process("sudo bash net/singleEndSetup.sh")
    check_return_code(acc_status, "Finalizing bridges and tap interfaces")

    if not os.path.exists(pidsDirectory):
        try:
            os.makedirs(pidsDirectory)
            check_return_code(0, "Creating pids directory")
        except OSError as e:
            check_return_code(1, e.strerror)

    time.sleep(1)
    print('Finished creating bridges and taps | Date now: %s' % datetime.datetime.now())

    #############################
    # Fourth, we create the bridges for the docker containers
    # https://docs.docker.com/v1.7/articles/networking/
    acc_status = 0
    for x in range(0, numberOfNodes):
        cmd = ['docker', 'inspect', '--format', "'{{ .State.Pid }}'", nameList[x]]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = p.communicate()
        pid = out[1:-2].strip()

        with open(pidsDirectory + nameList[x], "w") as text_file:
            text_file.write(str(pid, 'utf-8'))

        acc_status += process("bash net/container.sh %s %s" % (nameList[x], x), "Creating bridge side-int-X and side-ext-X for %s"%(nameList[x]), 0)

    # If something went wrong creating the bridges and tap interfaces, we panic and exit
    check_return_code(acc_status, "Creating all bridge side-int-X and side-ext-X" )
    # Old behaviour, but I got situations where this failed, who knows why and basically stopped everything
    # therefore I changed it to passive, if one fails, who cares but keep on going so the next simulations
    # dont break
    # check_return_code_chill(acc_status, "Creating bridge side-int-X and side-ext-X")

    print('Finished setting up bridges | Date now: %s' % datetime.datetime.now())
    print("Done.")

    return


################################################################################
# end create ()
################################################################################


################################################################################
# ns3 ()
################################################################################
def ns3(code = 0):
    print("NS3 ...")
    docker_files = 0
    verify_num_nodes()

    if os.path.exists(pidsDirectory + "ns3"):
        with open(pidsDirectory + "ns3", "rt") as in_file:
            text = in_file.read()
            if check_pid(int(text.strip())):
                print('NS3 is still running with pid = ' + text.strip())
                return

    total_emu_time = emulationTimeStr #(5 * 60) * numberOfNodes

    print('About to start NS3 RUN with total emulation time of %s' % str(total_emu_time))

    tmp = 'cd $NS3_HOME && '
    ns3_cmd = ''
    if networkStr == 'wifi':
        tmp += './ns3 run -j {0} "scratch/tap-vm --NumNodes={1} --TotalTime={2} --TapBaseName=emu '
        tmp += '--SizeX={3} --SizeY={3} --MobilitySpeed={4} --MobilityPause={5}"'
        ns3_cmd = tmp.format(jobs, numberOfNodesStr, total_emu_time, scenarioSize, nodeSpeed, nodePause)
    else:
        tmp += './ns3 run -j {0} "scratch/tap-vm --NumNodes={1} --TotalTime={2} --TapBaseName=emu '
        tmp += '--AnimationOn=false"'
        ns3_cmd = tmp.format(jobs, numberOfNodesStr, total_emu_time)

    print("NS3_HOME=%s && %s"% ((os.environ['NS3_HOME']).strip(), ns3_cmd))
    proc1 = subprocess.Popen(ns3_cmd, shell=True)

    time.sleep(5)
    print('proc1 = %s' % proc1.pid)

    with open(pidsDirectory + "ns3", "w") as text_file:
        text_file.write(str(proc1.pid))

    print('Running NS3 in the background | Date now: %s' % datetime.datetime.now())

    if code==1:
        return proc1

    return

################################################################################
# end ns3 ()
################################################################################


################################################################################
# run_emu ()
################################################################################
def run_emu():
    print("RUN SIM ...")
    verify_num_nodes()

    print('About to start RUN SIM | Date now: %s' % datetime.datetime.now())
    proc1 = None
    exec_code = 0

    if os.path.exists(pidsDirectory + "ns3"):
        with open(pidsDirectory + "ns3", "rt") as in_file:
            text = in_file.read()
            if check_pid(int(text.strip())):
                print('NS3 is still running with pid = ' + text.strip())
            else:
                print('NS3 is NOT running')
                exec_code = 1
                proc1 = ns3(exec_code)
                time.sleep(5)
    else:
        print('NS3 is NOT running')
        exec_code = 1
        proc1 = ns3(exec_code)
        time.sleep(5)

    print("Restarting containers")
    acc_status = 0
    for x in range(0, numberOfNodes):
        acc_status += process("docker restart -t 0 %s" % nameList[x], None, 0)
    check_return_code_chill(acc_status, "Restarting containers")

    #container_name_list = ""
    #for x in range(0, numberOfNodes):
    #    container_name_list += nameList[x]
    #    container_name_list += " "
    #acc_status = subprocess.call("docker restart -t 0 %s" % container_name_list, shell=True)
    #check_return_code_chill(acc_status, "Restarting containers")

    r_code = 0
    for x in range(0, numberOfNodes):
        if os.path.exists(pidsDirectory + nameList[x]):
            with open(pidsDirectory + nameList[x], "rt") as in_file:
                text = in_file.read()
                r_code = process("sudo rm -rf /var/run/netns/%s" % (text.strip()), "Destroying docker bridges for %s"%(nameList[x]), 0)

        cmd = ['docker', 'inspect', '--format', "'{{ .State.Pid }}'", nameList[x]]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        pid = out[1:-2].strip()

        with open(pidsDirectory + nameList[x], "w") as text_file:
            text_file.write(str(pid, 'utf-8'))

    check_return_code_chill(r_code, "Destroying all docker bridges")
    # syncConfigTime (s) = seconds + ~seconds
    sync_config_time = int(time.time()) + numberOfNodes
    write_conf(sync_config_time, numberOfNodes, timeoutStr, 1, 10001, "conf1.yml")

    acc_status = 0
    for x in range(0, numberOfNodes):
        acc_status += process("bash net/container.sh %s %s" % (nameList[x], x), "Creating new bridge side-int-X and side-ext-X for %s"%(nameList[x]), 0)

    check_return_code_chill(acc_status, "Cleaning old netns and setting up new")

    print('Finished RUN SIM | Date now: %s' % datetime.datetime.now())

    print('Letting the simulation run for %s' % emulationTimeStr)

    if exec_code == 1:
        proc1.communicate() # proc1.wait() 
    else:
        if os.path.exists(pidsDirectory + "ns3"):
            with open(pidsDirectory + "ns3", "rt") as in_file:
                text = in_file.read()
                while check_pid(int(text.strip())):
                    time.sleep(5)

    print('Finished RUN SIM 2 | Date now: %s' % datetime.datetime.now())

    return

################################################################################
# end run_emu ()
################################################################################


################################################################################
# destroy ()
################################################################################
def destroy():
    print("\nDestroying ...")
    global numberOfNodes
    if os.path.exists(pidsDirectory + "ns3"):
        with open(pidsDirectory + "ns3", "rt") as in_file:
            text = in_file.read()
            if os.path.exists("/proc/" + text.strip()):
                print("NS3 is running ... killing NS3 process")
                try:
                    os.killpg(os.getpgid(int(text.strip())), signal.SIGTERM)
                    check_return_code_chill(0, "Killing NS3 Process")
                except Exception as ex:
                    check_return_code_chill(1, "Killing NS3 Process\n"+ex)
            r_code = subprocess.call("sudo rm -rf %s" % (pidsDirectory +"ns3"), shell=True)
            check_return_code_chill(r_code, "Removing NS3 pid file")

    print("DESTROYING ALL CONTAINERS")

    r_containers = subprocess.check_output("docker ps -a -q", shell=True).decode('utf-8')
    r_code = 0
    if r_containers:
        r_containers = r_containers.strip().replace('\n',' ')
        r_code = subprocess.call("docker stop %s && docker rm %s"%(r_containers, r_containers), shell=True)
        check_return_code_chill(r_code, "Destroying ALL containers")
        '''
        # the following is slow
        r_containers = r_containers.strip().splitlines()
        for x in r_containers:
            r_code += process("docker stop %s"%(x), None, 0)
            r_code += process("docker rm %s"%(x), None, 0)
        check_return_code_chill(r_code, "Destroying ALL containers")
        '''

    r_code = process("sudo /etc/init.d/docker restart")

    docker_files = 0
    if os.path.exists(pidsDirectory):
        if os.listdir(pidsDirectory):
            docker_files =  nodes_in_pid_dir()
            if docker_files > numberOfNodes:
                numberOfNodes = docker_files
                nameList.clear()
                for x in range(0, numberOfNodes):
                    nameList.append(base_name + str(x + 1))

    r_code = 0
    for x in range(0, numberOfNodes):
        r_code += process("bash net/singleDestroy.sh %s" % (nameList[x]), "Destroying bridge and tap interface %s" % (nameList[x]), 0)
    check_return_code_chill(r_code, "Destroying bridge and tap interface")

    r_code = 0
    for x in range(0, numberOfNodes):
        if os.path.exists(pidsDirectory + nameList[x]):
            with open(pidsDirectory + nameList[x], "rt") as in_file:
                text = in_file.read()
                r_code += process("sudo rm -rf /var/run/netns/%s" % (text.strip()), "Destroying docker bridges %s" % (nameList[x]), 0)
    check_return_code_chill(r_code, "Destroying docker bridges")

    r_code = 0
    for x in range(0, numberOfNodes):
        r_code += process("sudo rm -rf %s" % (pidsDirectory + nameList[x]))
    check_return_code_chill(r_code, "Removing pids files")

    if os.path.exists(pidsDirectory):
        try:
            shutil.rmtree(pidsDirectory)
            check_return_code_chill(0, "Removing pids directory")
        except OSError as e:
            check_return_code_chill(1, "Removing pids directory\n"+e.strerror)

    return


################################################################################
# end destroy ()
################################################################################


if __name__ == '__main__':
    main()
