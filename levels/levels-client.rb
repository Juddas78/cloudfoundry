require 'thrift'
$:.push('gen-rb')
require 'can_-levels'

begin
	trans_ep = Thrift::Socket.new(ARGV[0], ARGV[1])
	trans_buf = Thrift::BufferedTrapsport.new(trans_ep)
	proto = Thrift::BinaryProtocol.new(trans_ep)
	client = CanLevels::Client.new(proto)

	trans_ep.open()
	client.update_can_level(42, 0.85)
	client.update_can_level(57, 0.89)
	res = client.get_cans_above_threshold(0.8)
	puts '[Client] recieved: ' + res.count.to_s
	puts res.inspect
	trans_ep.close()
rescue Thrift::Exception => tx
	print 'Thrift::Exception: ', tx.message, "/n"
end
	

