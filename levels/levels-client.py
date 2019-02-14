import sys
sys.path.append("gen-py")
from levels import CanLevels

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

trans = TSocket.TSocket("localhost", 9095)
trans = TTransport.TBufferedTransport(trans)
proto = TBinaryProtocol.TBinaryProtocol(trans)
client = CanLevels.Client(proto)

trans.open()
client.update_can_level(42, 0.85)
client.update_can_level(57, 0.89)
res = client.get_cans_above_threshold(0.8)
print("[Client] received: %d results" % (res.count))
print(res)
trans.close()
