/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/traffic-control-module.h"

#include <iostream>
#include <fstream>
#include <cmath>
#include <iomanip>
#include <algorithm>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("RedQlStandaloneSim");

class RedQlQueueDisc : public QueueDisc
{
public:
  static TypeId GetTypeId (void)
  {
    static TypeId tid = TypeId ("ns3::RedQlQueueDisc")
      .SetParent<QueueDisc> ()
      .SetGroupName ("TrafficControl")
      .AddConstructor<RedQlQueueDisc> ()
      .AddAttribute ("MinTh", "Minimum average length threshold in packets",
                     DoubleValue (30.0),
                     MakeDoubleAccessor (&RedQlQueueDisc::m_minTh),
                     MakeDoubleChecker<double> ())
      .AddAttribute ("MaxTh", "Maximum average length threshold in packets",
                     DoubleValue (90.0),
                     MakeDoubleAccessor (&RedQlQueueDisc::m_maxTh),
                     MakeDoubleChecker<double> ())
      .AddAttribute ("MaxP", "Maximum probability of dropping a packet",
                     DoubleValue (0.1),
                     MakeDoubleAccessor (&RedQlQueueDisc::m_maxP),
                     MakeDoubleChecker<double> ())
      .AddAttribute ("QW", "Queue weight related to the EWMA filter",
                     DoubleValue (0.002),
                     MakeDoubleAccessor (&RedQlQueueDisc::m_qW),
                     MakeDoubleChecker<double> ())
      .AddAttribute ("AqmVariant", "0: RED, 1: NLRED, 2: SmRED, 3: RED-QL",
                     UintegerValue (3),
                     MakeUintegerAccessor (&RedQlQueueDisc::m_aqmVariant),
                     MakeUintegerChecker<uint32_t> (0, 3))
      .AddAttribute ("MaxSize", "The maximum number of packets accepted by this queue disc",
                     QueueSizeValue (QueueSize ("250p")),
                     MakeQueueSizeAccessor (&QueueDisc::SetMaxSize,
                                            &QueueDisc::GetMaxSize),
                     MakeQueueSizeChecker ());
    return tid;
  }

  RedQlQueueDisc () : QueueDisc (QueueDiscSizePolicy::SINGLE_INTERNAL_QUEUE)
  {
    m_uv = CreateObject<UniformRandomVariable> ();
  }

  ~RedQlQueueDisc () override {}

  double GetQueueAvg (void) const { return m_qAvg; }

private:
  bool DoEnqueue (Ptr<QueueDiscItem> item) override
  {
    uint32_t nQueued = GetInternalQueue (0)->GetNPackets ();

    // 1. Tính kích thước hàng đợi trung bình ave (Công thức 1 - 3)
    if (nQueued == 0)
      {
        double idleSeconds = (Simulator::Now () - m_idleTime).GetSeconds ();
        double m = idleSeconds * (10000000.0 / (8.0 * 1000.0));
        m_qAvg = m_qAvg * std::pow (1.0 - m_qW, m);
      }
    else
      {
        m_qAvg = m_qAvg * (1.0 - m_qW) + (m_qW * nQueued);
      }

    // 2. Tính xác suất đánh rơi gói tin
    if (m_qAvg < m_minTh)
      {
        m_count = -1;
      }
    else if (m_qAvg >= m_minTh && m_qAvg < m_maxTh)
      {
        m_count++;
        double pb = CalculatePb (m_qAvg);
        double pa = (1.0 - (m_count * pb) > 0.0) ? (pb / (1.0 - (m_count * pb))) : 1.0;
        if (pa >= 1.0 || m_uv->GetValue (0.0, 1.0) < pa)
          {
            m_count = 0;
            DropBeforeEnqueue (item, "Random Early Drop");
            return false;
          }
      }
    else
      {
        m_count = 0;
        DropBeforeEnqueue (item, "Forced Drop (Above MaxTh)");
        return false;
      }

    if (nQueued >= GetMaxSize ().GetValue ())
      {
        DropBeforeEnqueue (item, "Buffer Overflow Drop");
        return false;
      }

    return GetInternalQueue (0)->Enqueue (item);
  }

  double CalculatePb (double ave)
  {
    double pb = 0.0;
    if (m_aqmVariant == 0) // Classic RED
      {
        pb = m_maxP * ((ave - m_minTh) / (m_maxTh - m_minTh));
      }
    else if (m_aqmVariant == 1) // NLRED
      {
        double ratio = (ave - m_minTh) / (m_maxTh - m_minTh);
        pb = (1.5 * m_maxP) * ratio * ratio;
      }
    else if (m_aqmVariant == 2) // SmRED
      {
        double target = m_minTh + (m_maxTh - m_minTh) / 2.0;
        double ratio = (ave - m_minTh) / (m_maxTh - m_minTh);
        if (ave < target)
          pb = m_maxP * ratio * ratio;
        else
          pb = m_maxP * std::sqrt (ratio);
      }
    else if (m_aqmVariant == 3) // RED-QL
      {
        double target = 2.0 * ((m_maxTh + m_minTh) / 3.0) - m_minTh;
        if (ave < target)
          {
            double term = (ave - m_minTh) / (2.0 * (m_maxTh - 2.0 * m_minTh));
            pb = 9.0 * m_maxP * term * term;
          }
        else
          {
            pb = m_maxP + 3.0 * (1.0 - m_maxP) * ((ave - target) / (m_maxTh + m_minTh));
          }
      }
    return std::clamp (pb, 0.0, 1.0);
  }

  Ptr<QueueDiscItem> DoDequeue (void) override
  {
    Ptr<QueueDiscItem> item = GetInternalQueue (0)->Dequeue ();
    if (GetInternalQueue (0)->IsEmpty ())
      {
        m_idleTime = Simulator::Now ();
      }
    return item;
  }

  Ptr<const QueueDiscItem> DoPeek (void) override
  {
    return GetInternalQueue (0)->Peek ();
  }

  bool CheckConfig (void) override
  {
    if (GetNInternalQueues () == 0)
      {
        AddInternalQueue (CreateObjectWithAttributes<DropTailQueue<QueueDiscItem>> (
            "MaxSize", QueueSizeValue (GetMaxSize ())));
      }
    return true;
  }

  void InitializeParams (void) override
  {
    m_qAvg = 0.0;
    m_count = -1;
    m_idleTime = Seconds (0.0);
  }

  double m_minTh;
  double m_maxTh;
  double m_maxP;
  double m_qW;
  uint32_t m_aqmVariant;

  double m_qAvg = 0.0;
  int32_t m_count = -1;
  Time m_idleTime = Seconds (0.0);
  Ptr<UniformRandomVariable> m_uv;
};

NS_OBJECT_ENSURE_REGISTERED (RedQlQueueDisc);

uint64_t g_totalRxBytes = 0;
std::ofstream g_qFile, g_delayFile, g_tputFile;

void RxPacketCallback (Ptr<const Packet> packet, const Address &from)
{
  g_totalRxBytes += packet->GetSize ();
}

void SampleMetrics (Ptr<RedQlQueueDisc> qDisc, double sampleInterval)
{
  double now = Simulator::Now ().GetSeconds ();
  double qAvg = qDisc->GetQueueAvg ();
  double delayMs = qAvg * 0.8;
  double tputMbps = (now > 0.0) ? ((g_totalRxBytes * 8.0) / (now * 1e6)) : 0.0;

  g_qFile     << std::fixed << std::setprecision (4) << now << "\t" << qAvg << "\n";
  g_delayFile << std::fixed << std::setprecision (4) << now << "\t" << delayMs << "\n";
  g_tputFile  << std::fixed << std::setprecision (4) << now << "\t" << tputMbps << "\n";

  if (now + sampleInterval <= 100.0)
    {
      Simulator::Schedule (Seconds (sampleInterval), &SampleMetrics, qDisc, sampleInterval);
    }
}

int main (int argc, char *argv[])
{
  uint32_t nSenders = 5;
  uint32_t aqmVariant = 3;
  double simTime = 100.0;
  std::string outDir = "scratch/red-ql-project/results/";
  std::string prefix = "RED-QL_Light";

  CommandLine cmd (__FILE__);
  cmd.AddValue ("nSenders", "Number of TCP sender nodes (5, 20, or 50)", nSenders);
  cmd.AddValue ("aqmVariant", "0:RED, 1:NLRED, 2:SmRED, 3:RED-QL", aqmVariant);
  cmd.AddValue ("prefix", "Output filename prefix", prefix);
  cmd.Parse (argc, argv);

  Config::SetDefault ("ns3::TcpL4Protocol::SocketType", StringValue ("ns3::TcpNewReno"));
  Config::SetDefault ("ns3::TcpSocket::SegmentSize", UintegerValue (1000));
  Config::SetDefault ("ns3::TcpSocket::DelAckCount", UintegerValue (1));

  NodeContainer senders, router, receiver;
  senders.Create (nSenders);
  router.Create (1);
  receiver.Create (1);

  PointToPointHelper accessLink, bottleneckLink;
  accessLink.SetDeviceAttribute ("DataRate", StringValue ("100Mbps"));
  accessLink.SetChannelAttribute ("Delay", StringValue ("5ms"));

  bottleneckLink.SetDeviceAttribute ("DataRate", StringValue ("10Mbps"));
  bottleneckLink.SetChannelAttribute ("Delay", StringValue ("100ms"));

  InternetStackHelper stack;
  stack.Install (senders);
  stack.Install (router);
  stack.Install (receiver);

  TrafficControlHelper tch;
  tch.SetRootQueueDisc ("ns3::RedQlQueueDisc",
                        "MinTh", DoubleValue (30.0),
                        "MaxTh", DoubleValue (90.0),
                        "MaxP", DoubleValue (0.1),
                        "QW", DoubleValue (0.002),
                        "AqmVariant", UintegerValue (aqmVariant),
                        "MaxSize", QueueSizeValue (QueueSize ("250p")));

  NetDeviceContainer bottleneckDevs = bottleneckLink.Install (router.Get (0), receiver.Get (0));
  QueueDiscContainer qDiscs = tch.Install (bottleneckDevs.Get (0));
  Ptr<RedQlQueueDisc> redQlDisc = DynamicCast<RedQlQueueDisc> (qDiscs.Get (0));

  Ipv4AddressHelper address;
  address.SetBase ("10.1.0.0", "255.255.255.0");
  Ipv4InterfaceContainer bottleneckIfs = address.Assign (bottleneckDevs);

  for (uint32_t i = 0; i < nSenders; ++i)
    {
      NetDeviceContainer sDevs = accessLink.Install (senders.Get (i), router.Get (0));
      std::ostringstream subnet;
      subnet << "10.2." << (i + 1) << ".0";
      address.SetBase (subnet.str ().c_str (), "255.255.255.0");
      address.Assign (sDevs);
    }

  Ipv4GlobalRoutingHelper::PopulateRoutingTables ();

  uint16_t port = 50000;
  PacketSinkHelper sinkHelper ("ns3::TcpSocketFactory",
                               InetSocketAddress (Ipv4Address::GetAny (), port));
  ApplicationContainer sinkApp = sinkHelper.Install (receiver.Get (0));
  sinkApp.Start (Seconds (0.0));
  sinkApp.Stop (Seconds (simTime));
  sinkApp.Get (0)->TraceConnectWithoutContext ("Rx", MakeCallback (&RxPacketCallback));

  for (uint32_t i = 0; i < nSenders; ++i)
    {
      BulkSendHelper source ("ns3::TcpSocketFactory",
                             InetSocketAddress (bottleneckIfs.GetAddress (1), port));
      source.SetAttribute ("MaxBytes", UintegerValue (0));
      source.SetAttribute ("SendSize", UintegerValue (1000));
      ApplicationContainer sourceApp = source.Install (senders.Get (i));
      sourceApp.Start (Seconds (0.0));
      sourceApp.Stop (Seconds (simTime));
    }

  g_qFile.open (outDir + prefix + "_queue.dat");
  g_delayFile.open (outDir + prefix + "_delay.dat");
  g_tputFile.open (outDir + prefix + "_tput.dat");

  Simulator::Schedule (Seconds (0.0), &SampleMetrics, redQlDisc, 0.1);

  Simulator::Stop (Seconds (simTime));
  Simulator::Run ();

  g_qFile.close ();
  g_delayFile.close ();
  g_tputFile.close ();
  Simulator::Destroy ();
  return 0;
}
