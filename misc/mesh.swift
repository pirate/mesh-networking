import Foundation
import MultipeerConnectivity

/*
swift mesh.swift bob
*/

// every instance needs a unique ID so that two can be run on the same machine
let instance_id: String

if CommandLine.arguments.count == 2 {
    instance_id = CommandLine.arguments[1]
}
else {
srandom(UInt32(time(nil)))
    instance_id = String(arc4random() % 1000);
}



class MESHPManagerDelegate {
    let known_devices: Set<MCPeerID>

    init() {
        self.known_devices = []
    }

    func devicesChanged(manager: MESHPManager, connectedDevices: [MCPeerID]) {
        print("[√] Devices", connectedDevices.map{$0.displayName})
        let new_devices = Set(connectedDevices).subtracting(self.known_devices)
        for device in new_devices {
            manager.send(data: "Hi new guy \(device.displayName)!", to: device)
        }
    }
    func recv(manager: MESHPManager, data: String, from: MCPeerID) {
        print("[>] RECV: \(data) from \(from.displayName)")
    }
}

class MESHPManager: NSObject {

    private let service_name = "MESP"  // bonjour service id

    private let myPeerId = MCPeerID(displayName: "\(Host.current().localizedName!)-\(instance_id)")

    private let advertiser: MCNearbyServiceAdvertiser
    private let browser: MCNearbyServiceBrowser

    var delegate: MESHPManagerDelegate

    lazy var session : MCSession = {
        let session = MCSession(peer: self.myPeerId, securityIdentity: nil, encryptionPreference: .required)
        session.delegate = self
        return session
    }()

    override init() {
        self.advertiser = MCNearbyServiceAdvertiser(peer: myPeerId, discoveryInfo: nil, serviceType: service_name)
        self.browser = MCNearbyServiceBrowser(peer: myPeerId, serviceType: service_name)
        self.delegate = MESHPManagerDelegate()

        super.init()

        self.advertiser.delegate = self
        self.advertiser.startAdvertisingPeer()

        self.browser.delegate = self
        self.browser.startBrowsingForPeers()
    }

    func send(data: String, to: MCPeerID) {
        print("[<] SEND: \(data) to \(to.displayName)")

        do {
            try self.session.send(data.data(using: .utf8)!, toPeers: [to], with: .reliable)
        }
        catch let error {
            print("[X] Error for sending: \(error)")
        }
    }

    deinit {
        self.advertiser.stopAdvertisingPeer()
        self.browser.stopBrowsingForPeers()
    }

}

extension MESHPManager : MCNearbyServiceAdvertiserDelegate {

    func advertiser(_ advertiser: MCNearbyServiceAdvertiser, didNotStartAdvertisingPeer error: Error) {
        print("[x] FAILED TO ADVERTISE SERVICE: \(error)")
    }

    func advertiser(_ advertiser: MCNearbyServiceAdvertiser, didReceiveInvitationFromPeer peerID: MCPeerID, withContext context: Data?, invitationHandler: @escaping (Bool, MCSession?) -> Void) {
        print("[+] GOT INVITE: from \(peerID.displayName)")
        invitationHandler(true, self.session)
    }

}

extension MESHPManager : MCNearbyServiceBrowserDelegate {
    func browser(_ browser: MCNearbyServiceBrowser, didNotStartBrowsingForPeers error: Error) {
        print("[x] FAILED TO BROWSE FOR PEERS: \(error)")
    }

    func browser(_ browser: MCNearbyServiceBrowser, foundPeer peerID: MCPeerID, withDiscoveryInfo info: [String : String]?) {
        print("[*] FOUND PEER: \(peerID.displayName)")
        print("[+] SENT INVITE: to \(peerID.displayName)")
        browser.invitePeer(peerID, to: self.session, withContext: nil, timeout: 10)
    }

    func browser(_ browser: MCNearbyServiceBrowser, lostPeer peerID: MCPeerID) {
        print("[-] LOST PEER: \(peerID.displayName)")
    }

}

extension MESHPManager : MCSessionDelegate {

    func session(_ session: MCSession, peer peerID: MCPeerID, didChange state: MCSessionState) {
        let states = [
            0: "disconnected",
            1: "connecting",
            2: "connected"
        ]
        print("[i] PEER \(peerID.displayName) CHANGED: to \(states[state.rawValue]!)")
        self.delegate.devicesChanged(manager: self, connectedDevices: session.connectedPeers)
    }

    func session(_ session: MCSession, didReceive data: Data, fromPeer peerID: MCPeerID) {
        let str = String(data: data, encoding: .utf8)!
        self.delegate.recv(manager: self, data: str, from: peerID)
    }

    func session(_ session: MCSession, didReceive stream: InputStream, withName streamName: String, fromPeer peerID: MCPeerID) {
        print("[>] RECV: (stream)")
    }

    func session(_ session: MCSession, didStartReceivingResourceWithName resourceName: String, fromPeer peerID: MCPeerID, with progress: Progress) {
        print("[>] RECV: (named resource)")
    }

    func session(_ session: MCSession, didFinishReceivingResourceWithName resourceName: String, fromPeer peerID: MCPeerID, at localURL: URL, withError error: Error?) {
        print("[>] RECV: (named resource)")
    }

}


let manager = MESHPManager()
print("You are \(instance_id). Welcome to Mesh Chat!")

let shouldKeepRunning = true

RunLoop.main.run(until: Date(timeIntervalSinceNow: 60))

// let rl = RunLoop.main
// while shouldKeepRunning && rl.run(mode: .defaultRunLoopMode, before: .distantFuture) {
//     print("input>")
//     // let response = readLine()!
//     print("got> \(response)")
// }

