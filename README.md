# DDoSim

## **Initial Setup:**

>**Note:** - The steps are verified on Ubuntu version 22.04 and Debian 11

1. Download “DDoSim” Project from: https://anonymous.4open.science/r/FFBE/

2. In DDoSim Directory, change the permission of the files as below: ``` sudo chmod +x -R * ```

3. Install DDoSim with below command:
   >**Note:** - Do not use sudo for the install command, it is placed wherever it is needed.

    ``` ./install.sh ```     

4. After Successful installation, Reboot the system


## Creation and network simulation of nodes(IoT Devices, Attacker, and Target Server):

  The framework uses a python script “main.py” to perform all the operations:

1. To check all the options available use command:

    ``` ./main.py --help ```

2. To Create number of nodes, use command:

    ``` ./main.py -n <nodes> create ```

    ``` e.g.,: ./main.py -n 3 create ```
    

3. To add the nodes to the NS3 network simulator, use command (the default simulation time is 600secs however it can be changed by using -t option):

    ``` ./main.py -n <nodes> ns3 ```

    ``` e.g.,: ./main.py -n 3 ns3 ```
    
    This will create the N Docker containers, bridges and tap interfaces, and will configure everything. Then it will start the NS3 process.

4. To emulate the created nodes, use command:

    ``` ./main.py -n <nodes> emulation ```

    ``` e.g.,: ./main.py -n 3 emulation ```
    
    This is the highly scalable part of the emulation. So what this does, is that it restarts the containers and makes sure everything is in place. By doing this, it restarts the app you are running inside the containers, allowing you to run a test. Then without destroying everything you just reinvoke the same command to start again.
    
## To Attack:

1. Open a new terminal and log into the attacker node the Command & Control server machine which controls bots.

    ``` docker exec -it emu1 bash ```

    ``` telnet 10.0.0.1 ```

    Username: root

    Password: root
  
2. To perform the DDoS attack, make sure that you have the entire nodes connected to the C&C server (you can see the total number of bots in the title bar of the C&C server). Type the following command in the C&C server terminal:
    
    ``` udpplain <TargetServer_IP> <duration_of_attack_in_sec> <options> ```

    ``` e.g.,: udpplain 10.0.0.4 100 dport=9 ```

3. Once the attack is done, the throughput file is created on the desktop with Left column: simulator time (in sec), Right column = throughput (overall received data at a given time).

## Destroy nodes:

1. The created nodes should be destroyed to create a different number of new nodes. To do so use the following command:

    ``` ./main.py -n <nodes> destroy ```
