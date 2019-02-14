import sys
sys.path.append("gen-py")

from thrift.transport import TTransport
from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from levels import CanLevels
from levels import ttypes

wcans = {}

class CanLevelsHandler:
    def get_cans_above_threshold(self, percent_full):
        return ttypes.can_levels(count=2, can_levels=wcans)

    def update_can_level(self, can_id, percent_full):
        wcans[can_id] = percent_full


handler = CanLevelsHandler()
proc = CanLevels.Processor(handler)
trans_ep = TSocket.TServerSocket(port=9095)
trans_fac = TTransport.TBufferedTransportFactory()
proto_fac = TBinaryProtocol.TBinaryProtocolFactory()
server = TServer.TThreadedServer(proc, trans_ep, trans_fac, proto_fac)

print("[Server] Started")
server.serve()
