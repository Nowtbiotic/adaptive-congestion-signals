#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"

#include <fstream>
#include <iostream>

using namespace ns3;

// ------------------------------------------------------------
// Output files
// ------------------------------------------------------------

std::ofstream throughputFile;
std::ofstream queueFile;
std::ofstream rttFile;
std::ofstream utilizationFile;

// ------------------------------------------------------------
// Throughput state
// ------------------------------------------------------------

uint64_t lastRxBytes = 0;

// ------------------------------------------------------------
// Utilization state
// ------------------------------------------------------------

uint64_t bottleneckTxBytes = 0;

// ------------------------------------------------------------
// Throughput measurement
// ------------------------------------------------------------

void
MeasureThroughput(Ptr<PacketSink> sink1,
                  Ptr<PacketSink> sink2)
{
    double now = Simulator::Now().GetSeconds();

    uint64_t totalRxBytes =
        sink1->GetTotalRx() +
        sink2->GetTotalRx();

    uint64_t bytesReceived =
        totalRxBytes - lastRxBytes;

    double throughputMbps =
        bytesReceived * 8.0 / 100000.0;

    throughputFile
        << now << ","
        << throughputMbps
        << "\n";

    lastRxBytes = totalRxBytes;

    Simulator::Schedule(
        MilliSeconds(100),
        &MeasureThroughput,
        sink1,
        sink2);
}

// ------------------------------------------------------------
// Bottleneck transmission callback
// ------------------------------------------------------------

void
BottleneckTx(Ptr<const Packet> packet)
{
    bottleneckTxBytes += packet->GetSize();
}

// ------------------------------------------------------------
// Utilization measurement
// ------------------------------------------------------------

void
MeasureUtilization()
{
    double now = Simulator::Now().GetSeconds();

    // 100 ms measurement interval.
    // Bottleneck capacity = 10 Mbps.
    double utilization =
        (bottleneckTxBytes * 8.0 / 100000.0) / 10.0;

    if (utilization > 1.0)
    {
        utilization = 1.0;
    }

    utilizationFile
        << now << ","
        << utilization
        << "\n";

    bottleneckTxBytes = 0;

    Simulator::Schedule(
        MilliSeconds(100),
        &MeasureUtilization);
}

// ------------------------------------------------------------
// Queue trace callback
// ------------------------------------------------------------

void
QueuePacketsInQueue(uint32_t oldValue,
                    uint32_t newValue)
{
    double now = Simulator::Now().GetSeconds();

    queueFile
        << now << ","
        << newValue
        << "\n";
}

// ------------------------------------------------------------
// RTT trace callback
// ------------------------------------------------------------

void
RttTrace(Time oldValue,
         Time newValue)
{
    double now = Simulator::Now().GetSeconds();

    rttFile
        << now << ","
        << newValue.GetMilliSeconds()
        << "\n";
}
void
ConnectRttTraces()
{
    Config::ConnectWithoutContext(
        "/NodeList/*/$ns3::TcpL4Protocol/SocketList/*/RTT",
        MakeCallback(&RttTrace));
}

// ------------------------------------------------------------
// Main
// ------------------------------------------------------------

int
main(int argc, char *argv[])
{
    Time::SetResolution(Time::NS);

    // --------------------------------------------------------
    // 1. Create nodes
    // --------------------------------------------------------

    NodeContainer senders;
    senders.Create(2);

    NodeContainer routers;
    routers.Create(2);

    NodeContainer receiver;
    receiver.Create(1);

    // --------------------------------------------------------
    // 2. Access links
    // --------------------------------------------------------

    PointToPointHelper access;

    access.SetDeviceAttribute(
        "DataRate",
        StringValue("100Mbps"));

    access.SetChannelAttribute(
        "Delay",
        StringValue("5ms"));

    NetDeviceContainer s1r1 =
        access.Install(
            senders.Get(0),
            routers.Get(0));

    NetDeviceContainer s2r1 =
        access.Install(
            senders.Get(1),
            routers.Get(0));

    // --------------------------------------------------------
    // 3. Bottleneck
    // --------------------------------------------------------

    PointToPointHelper bottleneck;

    bottleneck.SetDeviceAttribute(
        "DataRate",
        StringValue("10Mbps"));

    bottleneck.SetChannelAttribute(
        "Delay",
        StringValue("20ms"));

    NetDeviceContainer r1r2 =
        bottleneck.Install(
            routers.Get(0),
            routers.Get(1));

    // --------------------------------------------------------
    // 4. Receiver link
    // --------------------------------------------------------

    NetDeviceContainer r2d1 =
        access.Install(
            routers.Get(1),
            receiver.Get(0));

    // --------------------------------------------------------
    // 5. Internet stack
    // --------------------------------------------------------

    InternetStackHelper internet;

    internet.Install(senders);
    internet.Install(routers);
    internet.Install(receiver);

    // --------------------------------------------------------
    // 6. IP addresses
    // --------------------------------------------------------

    Ipv4AddressHelper address;

    address.SetBase(
        "10.1.1.0",
        "255.255.255.0");

    address.Assign(s1r1);

    address.SetBase(
        "10.1.2.0",
        "255.255.255.0");

    address.Assign(s2r1);

    address.SetBase(
        "10.1.3.0",
        "255.255.255.0");

    address.Assign(r1r2);

    address.SetBase(
        "10.1.4.0",
        "255.255.255.0");

    Ipv4InterfaceContainer receiverInterfaces =
        address.Assign(r2d1);

    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    // --------------------------------------------------------
    // 7. TCP Flow 1
    // --------------------------------------------------------

    uint16_t port1 = 5000;

    PacketSinkHelper sinkHelper1(
        "ns3::TcpSocketFactory",
        InetSocketAddress(
            Ipv4Address::GetAny(),
            port1));

    ApplicationContainer sinkApp1 =
        sinkHelper1.Install(receiver.Get(0));

    sinkApp1.Start(Seconds(0.0));
    sinkApp1.Stop(Seconds(40.0));

    OnOffHelper source1(
        "ns3::TcpSocketFactory",
        InetSocketAddress(
            receiverInterfaces.GetAddress(1),
            port1));

    source1.SetAttribute(
        "DataRate",
        DataRateValue(
            DataRate("50Mbps")));

    source1.SetAttribute(
        "PacketSize",
        UintegerValue(1000));

    source1.SetAttribute(
        "OnTime",
        StringValue(
            "ns3::ConstantRandomVariable[Constant=1]"));

    source1.SetAttribute(
        "OffTime",
        StringValue(
            "ns3::ConstantRandomVariable[Constant=0]"));

    ApplicationContainer sourceApp1 =
        source1.Install(senders.Get(0));

    sourceApp1.Start(Seconds(1.0));
    sourceApp1.Stop(Seconds(40.0));

    // --------------------------------------------------------
    // 8. TCP Flow 2
    // --------------------------------------------------------

    uint16_t port2 = 5001;

    PacketSinkHelper sinkHelper2(
        "ns3::TcpSocketFactory",
        InetSocketAddress(
            Ipv4Address::GetAny(),
            port2));

    ApplicationContainer sinkApp2 =
        sinkHelper2.Install(receiver.Get(0));

    sinkApp2.Start(Seconds(0.0));
    sinkApp2.Stop(Seconds(40.0));

    OnOffHelper source2(
        "ns3::TcpSocketFactory",
        InetSocketAddress(
            receiverInterfaces.GetAddress(1),
            port2));

    source2.SetAttribute(
        "DataRate",
        DataRateValue(
            DataRate("50Mbps")));

    source2.SetAttribute(
        "PacketSize",
        UintegerValue(1000));

    source2.SetAttribute(
        "OnTime",
        StringValue(
            "ns3::ConstantRandomVariable[Constant=1]"));

    source2.SetAttribute(
        "OffTime",
        StringValue(
            "ns3::ConstantRandomVariable[Constant=0]"));

    ApplicationContainer sourceApp2 =
        source2.Install(senders.Get(1));

    sourceApp2.Start(Seconds(1.0));
    sourceApp2.Stop(Seconds(40.0));

    // --------------------------------------------------------
    // 9. Open output files
    // --------------------------------------------------------

    throughputFile.open("throughput.csv");
    queueFile.open("queue.csv");
    rttFile.open("rtt.csv");
    utilizationFile.open("utilization.csv");

    throughputFile
        << "time,throughput_mbps\n";

    queueFile
        << "time,queue_packets\n";

    rttFile
        << "time,rtt_ms\n";

    utilizationFile
        << "time,utilization\n";

    // --------------------------------------------------------
    // 10. Get PacketSink objects
    // --------------------------------------------------------

    Ptr<PacketSink> sink1 =
        DynamicCast<PacketSink>(
            sinkApp1.Get(0));

    Ptr<PacketSink> sink2 =
        DynamicCast<PacketSink>(
            sinkApp2.Get(0));

    // --------------------------------------------------------
    // 11. Connect bottleneck transmission trace
    //
    // Router 1 = Node 2
    // Router 1 devices:
    //   Device 0 -> Sender 1
    //   Device 1 -> Sender 2
    //   Device 2 -> Router 2 (BOTTLENECK)
    // --------------------------------------------------------

    Config::ConnectWithoutContext(
        "/NodeList/2/DeviceList/2/"
        "$ns3::PointToPointNetDevice/MacTx",
        MakeCallback(&BottleneckTx));

    // --------------------------------------------------------
    // 12. Connect bottleneck queue trace
    // --------------------------------------------------------

    Config::ConnectWithoutContext(
        "/NodeList/2/DeviceList/2/"
        "$ns3::PointToPointNetDevice/TxQueue/"
        "PacketsInQueue",
        MakeCallback(&QueuePacketsInQueue));

    // --------------------------------------------------------
    // 13. Connect TCP RTT traces
    // --------------------------------------------------------
    Simulator::Schedule(
    Seconds(1.0),
    &ConnectRttTraces);

    // --------------------------------------------------------
    // 14. Start periodic measurements
    // --------------------------------------------------------

    Simulator::Schedule(
        Seconds(1.1),
        &MeasureThroughput,
        sink1,
        sink2);

    Simulator::Schedule(
        Seconds(1.1),
        &MeasureUtilization);

    // --------------------------------------------------------
    // 15. Run
    // --------------------------------------------------------

    Simulator::Stop(
        Seconds(40.0));

    Simulator::Run();

    Simulator::Destroy();

    // --------------------------------------------------------
    // 16. Close files
    // --------------------------------------------------------

    throughputFile.close();
    queueFile.close();
    rttFile.close();
    utilizationFile.close();

    std::cout
        << "\nSimulation completed successfully.\n";

    std::cout
        << "Real measurement files generated:\n"
        << "  throughput.csv\n"
        << "  queue.csv\n"
        << "  rtt.csv\n"
        << "  utilization.csv\n";

    return 0;
}
