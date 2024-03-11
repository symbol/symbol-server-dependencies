#include <zmq.h>
#include <cstdlib>
#include <iostream>
#include <stdexcept>

int main() try
{
	void *context = zmq_ctx_new();
	void *requester = zmq_socket(context, ZMQ_REQ);

	zmq_close(requester);
	zmq_ctx_destroy (context);

	return EXIT_SUCCESS;
}
catch (std::runtime_error & e) {
	std::cerr << e.what() << std::endl;
	return EXIT_FAILURE;
}
