#define C99

#include <cstdlib>
#include <iostream>

extern "C" {

//#include <amcl/arch.h>
#include <amcl/config_curve_BLS381.h>
#include <amcl/bls_BLS381.h>
#include <amcl/randapi.h>
}

#define G2LEN (4 * BFS_BLS381)

int main() {
	char* seedHex = "78d0fb6705ce77dee47d03eb5b9c5d30";
	char seedBuffer[16] = {0};
	octet seed = { sizeof(seedBuffer), sizeof(seedBuffer), seedBuffer};


	csprng rng;
    OCT_fromHex(&seed, seedHex);
    CREATE_CSPRNG(&rng, &seed);

    char sk1Buffer[BGS_BLS381];
    octet SK1 = {0, sizeof(sk1Buffer), sk1Buffer};
    char pk1Buffer[G2LEN];
    octet PK1 = {0, sizeof(pk1Buffer), pk1Buffer};

	char sk2Buffer[BGS_BLS381];
	octet SK2 = {0, sizeof(sk2Buffer), sk2Buffer};
	char pk2Buffer[G2LEN];
	octet PK2 = {0, sizeof(pk2Buffer), pk2Buffer};

	char sk3Buffer[BGS_BLS381];
	octet SK3 = {0, sizeof(sk3Buffer), sk3Buffer};
	char pk3Buffer[G2LEN];
	octet PK3 = {0, sizeof(pk3Buffer), pk3Buffer};


	BLS_BLS381_KEY_PAIR_GENERATE(&rng, &SK1, &PK1);
	BLS_BLS381_KEY_PAIR_GENERATE(&rng, &SK2, &PK2);
	BLS_BLS381_KEY_PAIR_GENERATE(&rng, &SK3, &PK3);


	printf("Private key SK1: ");
    OCT_output(&SK1);
    printf("Public key PK1: ");
    OCT_output(&PK1);
    printf("Private key SK2: ");
    OCT_output(&SK2);
    printf("Public key PK2: ");
    OCT_output(&PK2);
    printf("Private key SK3: ");
    OCT_output(&SK2);
    printf("Public key PK3: ");
    OCT_output(&PK2);
    printf("\n");

	return EXIT_SUCCESS;
}
