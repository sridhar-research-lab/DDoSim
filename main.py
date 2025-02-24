#!/usr/bin/env python3

import sys
import subprocess
import os
import errno
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
churn = '0'
ns3FileLog = '0'
scenarioSize = '5'
network = 'csma'
numberOfNodes = 0
devs=0
jobs = max(1, os.cpu_count() - 1)
nameList = []

baseContainerNameConn = 'myconnmanbox'
baseContainerNameDnsm = 'mydnsmasqbox'
baseContainerNameAtt = 'myattackbox'

pidsDirectory = "./var/pid/"

ns3Version=''
with open('network/ns3_version') as f:
    ns3Version = str.strip(f.readline())

def main():
    global numberOfNodesStr, \
        emulationTimeStr, \
        churn, \
        ns3FileLog, \
        network, \
        scenarioSize, \
        numberOfNodes, \
        nameList, \
        devs, \
        jobs

    ###############################
    # n == number of nodes
    # t == simulation time in seconds
    ###############################

    parser = argparse.ArgumentParser(description="DDoSim Implementation.", add_help=True)
    parser.add_argument("operation", action="store", type=str, choices=['create', 'ns3', 'emulation', 'destroy'], help="The name of the operation to perform, options: create, ns3, emulation, destroy")

    parser.add_argument("-n", "--number", action="store",type=int, help="The number of nodes to simulate")

    parser.add_argument("-t", "--time", action="store", type=int, help="The time in seconds of NS3 simulation")

    parser.add_argument("-net", "--network", action="store", type=str, choices=['csma', 'wifi'], help="The type of network, options: csma, wifi")

    parser.add_argument("-ch", "--churn", action="store", type=str, choices=['0', '1', '2'], help="Enable Nodes churn, options: 0, 1, or 2 ; these options are: no churn, static, or dynamic")

    parser.add_argument("-l", "--log", action="store", type=str, choices=['0', '1', '2'], help="Log from NS3 to File, options: 0, 1, or 2 ; these options are: no log, pcap only, or log pcap and statistics. If log is enabled, the files will be stored in desktop")

    parser.add_argument("-s", "--size", action="store", help="The size in meters of NS3 network simulation")

    parser.add_argument("-j", "--jobs", action="store", type=int, help="The number of parallel jobs")

    parser.add_argument('-v', '--version', action='version', version='%(prog)s 3.0')

    parser.add_argument("-d", "--devs", action="store", type=int, choices=[0 , 1 , 2], help="Used software for Devs, options: 0, 1, or 2 ; these options are: Connman, Dnsmasq, or both (Connman and Dnsmasq). If both is enabled, Devs will be assigned Connman or Dnsmasq randomly")

    args, unknown = parser.parse_known_args()

    if len(unknown):
        print('\x1b[6;30;41m' + '\nUnknown arument: ' +str(unknown)+ '\x1b[0m')
        parser.print_help()
        sys.exit(2)

    if args.number:
        numberOfNodesStr = args.number
    if args.time:
        emulationTimeStr = args.time
    if args.network:
        network = args.network
    if args.churn:
        churn = args.churn
    if args.log:
        ns3FileLog = args.log
    if args.size:
        scenarioSize = args.size
    if args.devs:
        devs = args.devs
    if args.jobs:
        jobs = int(args.jobs)

    operation = args.operation

    # Display input and output file name passed as the args
    print("\nOperation : %s" % operation)
    print("Number of nodes : %s" % numberOfNodesStr)
    print("Simulation time : %s" % emulationTimeStr)
    print("Network Type : %s" % network)
    print("Churn : %s" % ("no churn" if churn=='0' else "static churn" if churn=='1' else "dynamic churn"))
    print("NS3 File Log : %s" % ("disabled" if ns3FileLog=='0' else "enabled"))
    print("Devs : %s" % ("Connman" if devs==0 else "Dnsmasq" if devs==1 else "Connman and Dnsmasq"))

    if network == 'wifi':
        print("Scenario Size (Disk): %s" % (scenarioSize))

    print("\t")
    os.environ["NS3_HOME"] = "./network/ns-allinone-"+ns3Version+"/ns-"+ns3Version

    os.environ["DOCKER_CLI_EXPERIMENTAL"] = "enabled"

    numberOfNodes = int(numberOfNodesStr) + 1 # TServer

    if numberOfNodes < 3:
        print("number of nodes should be 2 or more")
        sys.exit(2)

    global base_name
    base_name = "emu"

    for x in range(0, numberOfNodes+2): # we are not using emu0 or emu1
        nameList.append(base_name + str(x))

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
            if docker_files != (numberOfNodes):
                print('Please correct the number of nodes (-n %d) in the command'%(docker_files))
                sys.exit(2)
        else:
            print("Run the 'create' command and try again")
            sys.exit(2)
    else:
        print("Run the 'create' command and try again")
        sys.exit(2)

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
    print("Creating ...\n")
    docker_files = 0
    if os.path.exists(pidsDirectory):
        if os.listdir(pidsDirectory):
            docker_files =  nodes_in_pid_dir()
            if (docker_files!=0):
                print("There are %d node(s) running. Run the 'destroy' command and try again"%(docker_files))
                return
    else:
        try:
            os.makedirs(pidsDirectory, exist_ok=True)
        except OSError as e:
            if errno.EEXIST != e.errno:
                raise

    #############################
    # First we make sure we are running the latest version of our Ubuntu container

    r_code = subprocess.call("DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 -t %s docker/Attacker/." % baseContainerNameAtt, shell=True)
    check_return_code(r_code, "Building attacker container %s" % baseContainerNameAtt)

    if devs == 0 or devs == 2 :
        r_code = subprocess.call("DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 -t %s docker/Devs_connman/." % baseContainerNameConn, shell=True)
        check_return_code(r_code, "Building nodes container %s" % baseContainerNameConn)

    if devs == 1 or devs == 2 :
        r_code = subprocess.call("DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 -t %s docker/Devs_dnsmasq/." % baseContainerNameDnsm, shell=True)
        check_return_code(r_code, "Building nodes container %s" % baseContainerNameDnsm)

    r_code = subprocess.call('[ -d "$NS3_HOME" ]', shell=True)
    if r_code !=0 :
        print("Unable to find NS3 in", (os.environ['NS3_HOME']), ", make sure the 'install.sh' file was executed correctly")
    check_return_code(r_code,"Checking NS3 directory")

    if network == 'wifi':
        r_code = subprocess.call("cd network && bash update.sh tap-wifi-virtual-machine.cc " + ns3Version, shell=True)
    else:
        r_code = subprocess.call("cd network && bash update.sh tap-csma-virtual-machine.cc " + ns3Version, shell=True)

    check_return_code(r_code,"Copying latest ns3 file")

    print("NS3 up to date!")
    print("Go to NS3 folder: cd %s" %(os.environ['NS3_HOME']))

    r_code = subprocess.call("cd $NS3_HOME && ./ns3 build -j {}".format(jobs), shell=True)

    if r_code !=0 :
        print("Unable to build NS3 in", (os.environ['NS3_HOME']), ", let's try to reconfigure. Then, try again~")
        r_code = subprocess.call("cd $NS3_HOME && ./ns3 clean &&./ns3 configure --enable-sudo --disable-examples --disable-tests --disable-python --build-profile=optimized && ./ns3 build -j {}".format(jobs), shell=True)

    check_return_code(r_code,"NS3 BUILD")

    print('NS3 Build finished | Date now: %s' % datetime.datetime.now())

    #############################
    # We run the numberOfNodes of containers.
    # https://docs.docker.com/engine/reference/run/
    # They have to run as privileged (to have access to all host devices, might be unsafe, will check later)
    # By default, Docker containers are "unprivileged" and cannot, for example,
    # run a Docker daemon inside a Docker container. This is because by default a container is not allowed to
    # access any devices, but a "privileged" container is given access to all devices.
    # -dit ... -d run as daemon, -i Keep STDIN open even if not attached, -t Allocate a pseudo-tty
    # --name the name of the container, using emuX
    # Finally the name of our own Ubuntu image.

    dir_path = os.path.dirname(os.path.realpath(__file__))

    # https://github.com/dperson/openvpn-client/issues/75
    acc_status = 0
    acc_status = process("docker run --platform linux/amd64 --restart=always --sysctl net.ipv6.conf.all.disable_ipv6=0 --privileged -dit --net=none --name %s %s" % (nameList[2], baseContainerNameAtt), None, 1)

    selected = 1
    for x in range(3, (numberOfNodes+1)):
        if devs == 1:
            selected = 2
        elif devs == 2:
            selected = random.choice([1, 2]) # Connman or Dnsmasq

        if selected ==1:
            acc_status += process("docker run --platform linux/amd64 --restart=always --sysctl net.ipv6.conf.all.disable_ipv6=0 --privileged -dit --net=none --name %s %s" % (nameList[x], baseContainerNameConn), None, 0)
        else:
            acc_status += process("docker run --platform linux/amd64 --restart=always --sysctl net.ipv6.conf.all.disable_ipv6=0 --privileged -dit --net=none --name %s %s" % (nameList[x], baseContainerNameDnsm), None, 0)

    # If something went wrong running the docker containers, we panic and exit
    check_return_code(acc_status, "Running docker containers")

    time.sleep(1)
    print('Finished running containers | Date now: %s' % datetime.datetime.now())

    #############################
    # we create the bridges and the tap interfaces for NS3
    # Based on NS3 scripts ... https://www.nsnam.org/docs/release/3.25/doxygen/tap-wifi-virtual-machine_8cc.html
    # But in the source you can find more examples in the same dir.
    acc_status = 0
    for x in range(2, numberOfNodes+1):
        acc_status += process("bash connections/singleSetup.sh %s" % (nameList[x]), None, 0)

    check_return_code(acc_status, "Creating bridge and tap interface")

    acc_status += process("sudo bash connections/singleEndSetup.sh")
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
    # we create the bridges for the docker containers
    # https://docs.docker.com/v1.7/articles/networking/
    acc_status = 0
    for x in range(2, numberOfNodes+1):
        cmd = ['docker', 'inspect', '--format', "'{{ .State.Pid }}'", nameList[x]]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = p.communicate()
        pid = out[1:-2].strip()

        with open(pidsDirectory + nameList[x], "w") as text_file:
            text_file.write(str(pid, 'utf-8'))

        acc_status += process("bash connections/container.sh %s %s" % (nameList[x], x), "Creating bridge side-int-X and side-ext-X for %s"%(nameList[x]), 0)

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
    print("NS3 ...\n")
    docker_files = 0
    verify_num_nodes()

    if os.path.exists(pidsDirectory + "ns3"):
        with open(pidsDirectory + "ns3", "rt") as in_file:
            text = in_file.read()
            if check_pid(int(text.strip())):
                print('NS3 is still running with pid = ' + text.strip())
                return

    total_emu_time = emulationTimeStr

    print('About to start NS3 RUN with total emulation time of %s' % str(total_emu_time))

    tmp = 'cd $NS3_HOME && '
    ns3_cmd = ''
    if network == 'wifi':
        tmp += './ns3 run -j {0} "scratch/tap-vm --NumNodes={1} --TotalTime={2} --TapBaseName=emu '
        tmp += '--DiskDistance={3} --Churn={4} --FileLog={5}"'
        ns3_cmd = tmp.format(jobs, str(numberOfNodes), total_emu_time, scenarioSize, churn, ns3FileLog)
    else:
        tmp += './ns3 run -j {0} "scratch/tap-vm --NumNodes={1} --TotalTime={2} --Churn={3} --FileLog={4} --TapBaseName=emu '
        tmp += '--AnimationOn=false"'
        ns3_cmd = tmp.format(jobs, str(numberOfNodes), total_emu_time, churn, ns3FileLog)

    print("NS3_HOME=%s && %s"% ((os.environ['NS3_HOME']).strip(), ns3_cmd))

    import getpass
 
    try:
        p = getpass.getpass(prompt='Sudo password:')
    except Exception as error:
        print('ERROR', error)

    from tempfile import SpooledTemporaryFile as tempfile
    f = tempfile()
    f.write((p+'\n').encode('utf-8'))
    f.seek(0)

    proc1 = subprocess.Popen(ns3_cmd,stdin=f,shell=True)
    f.close()
    time.sleep(10)
    proc1.poll()
    input('\nPress the Enter key to continue...')

    '''
    #https://stackoverflow.com/questions/54319960/wait-for-a-prompt-from-a-subprocess-before-sending-stdin-input
    proc1 = subprocess.Popen(ns3_cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    import pexpect.fdpexpect
    o=pexpect.fdpexpect.fdspawn(proc1.stdout.fileno())
    o.expect("Sudo password:\n")
    proc1.stdin.write(p+'\n')
    proc1.stdin.close()
    print(proc1.stdout.read())
    '''

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
    print("RUN SIM ...\n")
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
    for x in range(2, numberOfNodes+1):
        acc_status += process("docker restart -t 0 %s" % nameList[x], None, 0)
    check_return_code_chill(acc_status, "Restarting containers")

    #container_name_list = ""
    #for x in range(0, numberOfNodes):
    #    container_name_list += nameList[x]
    #    container_name_list += " "
    #acc_status = subprocess.call("docker restart -t 0 %s" % container_name_list, shell=True)
    #check_return_code_chill(acc_status, "Restarting containers")

    r_code = 0
    for x in range(2, numberOfNodes+1):
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

    acc_status = 0
    for x in range(2, numberOfNodes+1):
        acc_status += process("bash connections/container.sh %s %s" % (nameList[x], x), "Creating new bridge side-int-X and side-ext-X for %s"%(nameList[x]), 0)

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
    print("Destroying ...\n")
    global numberOfNodes
    if os.path.exists(pidsDirectory + "ns3"):
        with open(pidsDirectory + "ns3", "rt") as in_file:
            text = in_file.read()
            if os.path.exists("/proc/" + text.strip()):
                print("NS3 is running ... killing the NS3 process")
                try:
                    os.killpg(os.getpgid(int(text.strip())), signal.SIGTERM)
                    check_return_code_chill(0, "Killing the NS3 Process")
                except Exception as ex:
                    check_return_code_chill(1, "Killing the NS3 Process\n"+ex)
            r_code = subprocess.call("sudo rm -rf %s" % (pidsDirectory +"ns3"), shell=True)
            check_return_code_chill(r_code, "Removing the NS3 pid file")

    print("DESTROYING ALL CONTAINERS")

    r_containers = subprocess.check_output("docker ps -a -q", shell=True).decode('utf-8')
    r_code = 0
    if r_containers:
        r_containers = r_containers.strip().replace('\n',' ')
        r_code = subprocess.call("docker stop %s && docker rm %s"%(r_containers, r_containers), shell=True)
        check_return_code_chill(r_code, "Destroying ALL containers")

    r_code = process("sudo /etc/init.d/docker restart")

    docker_files = 0
    if os.path.exists(pidsDirectory):
        if os.listdir(pidsDirectory):
            docker_files =  nodes_in_pid_dir()
            if docker_files > numberOfNodes:
                numberOfNodes = docker_files
                nameList.clear()
                for x in range(1, numberOfNodes):
                    nameList.append(base_name + str(x + 1))

    r_code = 0
    for x in range(2, numberOfNodes+1):
        r_code += process("bash connections/singleDestroy.sh %s" % (nameList[x]), "Destroying bridge and tap interface %s" % (nameList[x]), 0)
    check_return_code_chill(r_code, "Destroying bridge and tap interface")

    r_code = 0
    for x in range(2, numberOfNodes+1):
        if os.path.exists(pidsDirectory + nameList[x]):
            with open(pidsDirectory + nameList[x], "rt") as in_file:
                text = in_file.read()
                r_code += process("sudo rm -rf /var/run/netns/%s" % (text.strip()), "Destroying docker bridges %s" % (nameList[x]), 0)
    check_return_code_chill(r_code, "Destroying docker bridges")

    r_code = 0
    for x in range(1, numberOfNodes+1):
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
