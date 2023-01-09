/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

//
// This is an illustration of how one could use virtualization techniques to
// allow running applications on virtual machines talking over simulated
// networks.
//
// The actual steps required to configure the virtual machines can be rather
// involved, so we don't go into that here.  Please have a look at one of
// our HOWTOs on the nsnam wiki for more details about how to get the 
// system confgured.  For an example, have a look at "HOWTO Use Linux 
// Containers to set up virtual networks" which uses this code as an 
// example.
//
// The configuration you are after is explained in great detail in the 
// HOWTO, but looks like the following:
//
//  +----------+                           +----------+
//  | virtual  |                           | virtual  |
//  |  Linux   |                           |  Linux   |
//  |   Host   |                           |   Host   |
//  |          |                           |          |
//  |   eth0   |                           |   eth0   |
//  +----------+                           +----------+
//       |                                      |
//  +----------+                           +----------+
//  |  Linux   |                           |  Linux   |
//  |  Bridge  |                           |  Bridge  |
//  +----------+                           +----------+
//       |                                      |
//  +------------+                       +-------------+
//  | "tap-left" |                       | "tap-right" |
//  +------------+                       +-------------+
//       |           n0            n1           |
//       |       +--------+    +--------+       |
//       +-------|  tap   |    |  tap   |-------+
//               | bridge |    | bridge |
//               +--------+    +--------+
//               |  CSMA  |    |  CSMA  |
//               +--------+    +--------+
//                   |             |
//                   |             |
//                   |             |
//                   ===============
//                      CSMA LAN
//

#include <iostream>
#include <fstream>
#include <iomanip>
#include <limits>
#include <time.h>

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/csma-module.h"
#include "ns3/tap-bridge-module.h"

#include "ns3/netanim-module.h"

#include "ns3/internet-module.h"
#include "ns3/ipv4-global-routing-helper.h"
#include "ns3/applications-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("TapCsmaVirtualMachineExample");

class TargetServer : public Application
{
public:

  TargetServer();
  virtual ~TargetServer();

  Ptr<Socket> GetListeningSocket(void) const;

  void Setup(uint16_t Port, int numnodes);

protected:
  virtual void DoDispose(void);

private:
  virtual void StartApplication(void);
  virtual void StopApplication(void);

  void OutData(void);

  void HandleAccept(Ptr<Socket> socket, const Address& from);
  void HandleRead(Ptr<Socket> socket);
  void HandlePeerClose(Ptr<Socket> socket);
  void HandlePeerError(Ptr<Socket> socket);
  void Initiate(void);

  Ptr<Socket>       m_socket;
  //Ptr<Socket>     s_socket;

  Address           tx_peer;
  TypeId            tid;
  Address           local;

  //int             packet_count;
  double            totalBytes;
  double            startStastics;
  double            endStastics;
  std::ofstream     myAppData;
  char              thrName[500];
  Time              collect;
  EventId           m_collectEvent;
};
TargetServer::TargetServer()
  : m_socket(0),
    //s_socket(0),
    local()
{
}

TargetServer::~TargetServer()
{
  m_socket = 0;
  //s_socket = 0;
  if (myAppData.is_open())
  {
    myAppData.close();
  }
}


Ptr<Socket>
TargetServer::GetListeningSocket(void) const
{
  return m_socket;
}

void
TargetServer::DoDispose(void)
{
  std::cout<<"\n\n****************************************\n"
  <<"Simulation Time: "<<(Simulator::Now ().As (Time::S))<<" NS3 finished running"
  <<"\n****************************************\n\n";
  Simulator::Cancel (m_collectEvent);
  m_socket = 0;
  //s_socket = 0;
  // chain up
  Application::DoDispose();
}

void
TargetServer::StartApplication() // Called at time specified by Start
{
  if (m_socket == 0)
  {
    m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
    //InetSocketAddress local = InetSocketAddress (Ipv4Address::GetAny (), m_port);
    if (m_socket->Bind (local) == -1)
    {
        NS_FATAL_ERROR ("Failed to bind socket");
    }

    m_socket->Listen();
    //m_socket->ShutdownSend();
  }

  /*s_socket->Bind();
  s_socket->Connect(tx_peer);
  s_socket->ShutdownRecv();*/

  m_socket->SetRecvCallback(MakeCallback(&TargetServer::HandleRead, this));
  m_socket->SetAcceptCallback(
      MakeNullCallback<bool, Ptr<Socket>, const Address &>(),
      MakeCallback(&TargetServer::HandleAccept, this));
  m_socket->SetCloseCallbacks(
      MakeCallback(&TargetServer::HandlePeerClose, this),
      MakeCallback(&TargetServer::HandlePeerError, this));
}

void
TargetServer::StopApplication() // Called at time specified by Stop
{
  Simulator::Cancel (m_collectEvent);
  if (m_socket != 0)
  {
    m_socket->Close();
    m_socket->SetRecvCallback(MakeNullCallback<void, Ptr<Socket> >());
  }

  /*if (s_socket)
  {
    s_socket->Close();
  }*/
}

void
TargetServer::HandleRead(Ptr<Socket> socket)
{
  //int imageLineNumber,q,myDatasize;
  Ptr<Packet> packet;
  Address from;
  Address localAddress;
  while ((packet = socket->RecvFrom(from)))
  {
    //Payload payload;//to hold recievd data
    socket->GetSockName (localAddress);

    if (packet->GetSize() == 0)
    { //EOF
      break;
    }

    /*packet->CopyData((uint8_t*)&payload, sizeof(Payload));
    nodeid = payload.source_id;

    payload.mec_id = m_id;

    
    if (Simulator::Now() > (collect))
    {
      Ptr<Packet> spacket = Create<Packet>((uint8_t*)&payload, packet->GetSize());
      s_socket->Send(spacket);
    }*/

    //start my statistics
    if (Simulator::Now() > (collect))
    {
      totalBytes += packet->GetSize ();
      endStastics = Simulator::Now().ToDouble(ns3::Time::MS);
      //packet_count ++;
      //delay += (Simulator::Now() - payload.timestamp);
    }

  

    if (InetSocketAddress::IsMatchingType(from))
    {
      NS_LOG_DEBUG("At time " << Simulator::Now ().As (Time::S)
                  << " server received " << packet->GetSize()
                  << " bytes from " << InetSocketAddress::ConvertFrom(from).GetIpv4()
                  << " port " << InetSocketAddress::ConvertFrom(from).GetPort());
    }

    //packet->RemoveAllPacketTags ();
    //packet->RemoveAllByteTags ();
    //NS_LOG_LOGIC ("Echoing packet");
    //socket->SendTo (packet, 0, from);
  }
}

void
TargetServer::HandlePeerClose(Ptr<Socket> socket)
{
  NS_LOG_FUNCTION(this << socket);
}

void
TargetServer::HandlePeerError(Ptr<Socket> socket)
{
  NS_LOG_FUNCTION(this << socket);
}

void
TargetServer::HandleAccept(Ptr<Socket> s, const Address& from)
{
  s->SetRecvCallback(MakeCallback(&TargetServer::HandleRead, this));
}

void
TargetServer::Setup(uint16_t m_port, int numnodes)
{
  //tx_peer = address;//cloud address
  //s_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());

  local = InetSocketAddress(Ipv4Address::GetAny(), m_port);
  collect = Seconds(10);

  startStastics =  collect.ToDouble(ns3::Time::MS);
  totalBytes = 0.0;
  endStastics = 0.0;
  //packet_count = 0;


  // the following is to obtain desktop dir to store simulation output
  char outputDir[200];
  FILE *f = popen("echo ~/Desktop", "r");
  while (fgets(outputDir, 100, f) != NULL) {}
  pclose(f);

  size_t ln = strlen(outputDir) - 1;
  if (*outputDir && outputDir[ln] == '\n')
    outputDir[ln] = '\0';

  //std::string outputd = string (outputDir);//dedicated output location variable

  sprintf(thrName, "%s/%d_throughput.txt", outputDir,numnodes);

  //if file exists, then remove it
  std::ifstream fstr(thrName);
  if (fstr.good())
  {
    std::remove(thrName);
  }
 
  m_collectEvent = Simulator::Schedule (Seconds(1.0), &TargetServer::OutData, this);
}

void
TargetServer::OutData(void)
{
  //std::cout << Simulator::Now().ToDouble(ns3::Time::S) << " TServer Collecting Data" << "\n";
  if (Simulator::Now() > (collect))
  {
    myAppData.open(thrName, std::ios::app);
    double duration = (endStastics - startStastics) / 1000.0;

    if (!myAppData.is_open())
    {
      NS_FATAL_ERROR ("Unable to create a file to store the output");
    }

    myAppData << std::setprecision(2) << Simulator::Now().ToDouble(ns3::Time::S) << "\t" << std::fixed
                 << std::setprecision(9) << ((totalBytes == 0.0) ? 0.0 : ((totalBytes * 8.0 ) / duration)) << "\n";

    startStastics = Simulator::Now().ToDouble(ns3::Time::MS);
    totalBytes = 0.0;
    myAppData.close();

    //delay = NanoSeconds(0);
    //packet_count = 0;
  }
  m_collectEvent = Simulator::Schedule (Seconds(1.0), &TargetServer::OutData, this);
}

int 
main (int argc, char *argv[])
{
  bool AnimationOn = false;
  int NumNodes = 10;
  double TotalTime = 600.0;

  std::string TapBaseName = "emu";

  //LogComponentEnable ("CsmaNetDevice",   LOG_LEVEL_ALL);
  //LogComponentEnable ("UdpEchoServerApplication", LOG_LEVEL_INFO);
  //LogComponentEnable ("TapCsmaVirtualMachineExample", LOG_LEVEL_ALL);
  LogComponentEnable ("TapCsmaVirtualMachineExample", LOG_LEVEL_DEBUG);

  CommandLine cmd;
  cmd.AddValue ("NumNodes", "Number of nodes/devices", NumNodes);
  cmd.AddValue ("TotalTime", "Total simulation time", TotalTime);
  cmd.AddValue ("TapBaseName", "Base name for tap interfaces", TapBaseName);
  cmd.AddValue ("AnimationOn", "Enable animation", AnimationOn);

  cmd.Parse (argc,argv);

  //
  // We are interacting with the outside, real, world.  This means we have to 
  // interact in real-time and therefore means we have to use the real-time
  // simulator and take the time to calculate checksums.
  //
  GlobalValue::Bind ("SimulatorImplementationType", StringValue ("ns3::RealtimeSimulatorImpl"));
  GlobalValue::Bind ("ChecksumEnabled", BooleanValue (true));

  NS_LOG_UNCOND ("Running simulation in csma mode");

  //
  // Create two ghost nodes.  The first will represent the virtual machine host
  // on the left side of the network; and the second will represent the VM on 
  // the right side.
  //
  NS_LOG_INFO("Creating nodes");
  NodeContainer nodes;
  nodes.Create (NumNodes+1);// +1 for TServer

  //
  // Use a CsmaHelper to get a CSMA channel created, and the needed net 
  // devices installed on both of the nodes.  The data rate and delay for the
  // channel can be set through the command-line parser.  For example,
  //
  // ./waf --run "tap=csma-virtual-machine --ns3::CsmaChannel::DataRate=10000000"
  //
  CsmaHelper csma;
  //csma.SetChannelAttribute ("DataRate",  StringValue("500GBps"));//DataRateValue (5000000));
  //csma.SetChannelAttribute ("Delay", TimeValue (MilliSeconds (2)));

  NetDeviceContainer devices = csma.Install (nodes);

  InternetStackHelper internetRight;
  internetRight.Install (nodes);

  Ipv4AddressHelper ipv4Right;
  ipv4Right.SetBase ("10.0.0.0", "255.0.0.0");
  Ipv4InterfaceContainer interfacesRight = ipv4Right.Assign (devices);

  //
  // Use the TapBridgeHelper to connect to the pre-configured tap devices for 
  // the left side.  We go with "UseBridge" mode since the CSMA devices support
  // promiscuous mode and can therefore make it appear that the bridge is 
  // extended into ns-3.  The install method essentially bridges the specified
  // tap to the specified CSMA device.
  //
  NS_LOG_INFO("Creating tap bridges");
  TapBridgeHelper tapBridge;
  tapBridge.SetAttribute ("Mode", StringValue ("UseBridge"));

  for (int i = 0; i < NumNodes; i++)
  {
    std::stringstream tapName;
    tapName << "tap-" << TapBaseName << (i+1) ;
    NS_LOG_INFO("Tap bridge = " + tapName.str ());

    tapBridge.SetAttribute ("DeviceName", StringValue (tapName.str ()));
    tapBridge.Install (nodes.Get (i), devices.Get (i));

    //set data rate for the csma netdevice
    /*Ptr<CsmaNetDevice> PtrCsmaNetDevice = DynamicCast<CsmaNetDevice>(devices.Get(i));
    if (i != 0) // 0 is the attacker
    {
      RngSeedManager::SetSeed(time(NULL));  // Changes seed from default of 1 to 3
      RngSeedManager::SetRun(time(NULL));   // Changes run number from default of 1 to 7
      Ptr<UniformRandomVariable> x = CreateObject<UniformRandomVariable>();

      //NS_LOG_UNCOND ("Node = "<<i<<" Bef DataRate " << (PtrCsmaNetDevice->GetDataRate()));

      PtrCsmaNetDevice->SetDataRate(DataRate(x->GetValue(1000000.0, 30000000.0)));
      //Ptr<CsmaChannel> PtrCsmaChannel = DynamicCast<CsmaChannel>(devices.Get(i)->GetChannel());
      //NS_LOG_UNCOND ("Node = "<<i<<" Bef DataRate " << (PtrCsmaChannel->GetDataRate()));
      //PtrCsmaChannel->SetAttribute("DataRate", DataRateValue (5000000));
    }
    NS_LOG_UNCOND ("Node = "<<i<<" DataRate " << (PtrCsmaNetDevice->GetDataRate()));*/
  }

  uint16_t port = 9;  // well-known echo port number
  //UdpEchoServerHelper server (port);
  //ApplicationContainer apps = server.Install (nodes.Get (NumNodes));
  //apps.Start (Seconds (1));
  //apps.Stop (Seconds (TotalTime));

  NS_LOG_INFO("Creating Taregt Server Application");
  Ptr<TargetServer> tServer = CreateObject<TargetServer>();
  nodes.Get (NumNodes)->AddApplication(tServer);
  tServer->Setup(port, (NumNodes - 1));
  tServer->SetStartTime(Seconds(0.));
  tServer->SetStopTime(Seconds(TotalTime));

  {
    Ptr <Node> PtrNode = nodes.Get (NumNodes);
    Ptr<NetDevice> PtrNetDevice = PtrNode->GetDevice(0);
    Ptr<Ipv4> ipv4 = PtrNode->GetObject<Ipv4> ();
    Ipv4InterfaceAddress iaddr = ipv4->GetAddress (1,0);
    Ipv4Address ipAddr = iaddr.GetLocal ();

    std::cout<<"\n****************************************\nTarget Server IPv4: "
    <<ipAddr<<"\nTarget Server MAC:"<<(PtrNetDevice->GetAddress())
    <<"\n****************************************\n\n";
  }


  if( AnimationOn )
  {
    NS_LOG_UNCOND ("Activating Animation");
    AnimationInterface anim ("animation.xml"); // Mandatory 
    for (uint32_t i = 0; i < nodes.GetN (); ++i)
      {
        std::stringstream ssi;
        ssi << i;
        anim.UpdateNodeDescription (nodes.Get (i), "Node" + ssi.str()); // Optional
        anim.UpdateNodeColor (nodes.Get (i), 255, 0, 0); // Optional
      }

    anim.EnablePacketMetadata (); // Optional
    // anim.EnableIpv4RouteTracking ("routingtable-wireless.xml", Seconds (0), Seconds (5), Seconds (0.25)); //Optional
    anim.EnableWifiMacCounters (Seconds (0), Seconds (TotalTime)); //Optional
    anim.EnableWifiPhyCounters (Seconds (0), Seconds (TotalTime)); //Optional
  }

  //
  // Run the simulation for TotalTime seconds to give the user time to play around
  //
  Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

  Simulator::Stop (Seconds (TotalTime));
  Simulator::Run ();
  Simulator::Destroy ();
}