#include <cstdlib>
#include <iostream>

#include <mongoc/mongoc.h>

int main()
{
	bson_t *insert;

	mongoc_init();

	mongoc_client_t *client = NULL;

	insert = BCON_NEW("Hello", BCON_UTF8("World"));


	bson_destroy(insert);
	mongoc_cleanup();

	return EXIT_SUCCESS;
}
