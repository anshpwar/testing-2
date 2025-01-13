#ifndef LK_IBAN_H
#define LK_IBAN_H

#include <stddef.h>
#include <stdint.h>

#include "lk_money.h"

/* Result of splitting an IBAN into its parts. */
typedef struct lk_iban_info {
    char country[4];
    int32_t check_digits;
    int32_t length;
    int32_t expected_length;
} lk_iban_info;

size_t lk_iban_info_sizeof(void);

/* Registered IBAN length for a two-letter country code, or LK_ERR_IBAN_COUNTRY. */
int lk_iban_expected_length(const char *country);

/* ISO 7064 mod 97-10 remainder of the rearranged IBAN (1 for a valid IBAN), or a negative status. */
int lk_iban_mod97(const char *iban);

/* LK_OK when format, country length and checksum are all correct. */
int lk_iban_validate(const char *iban);

/* Writes the two check digits for country + bban into out[0..2] (NUL terminated). */
int lk_iban_check_digits(const char *country, const char *bban, char *out);

int lk_iban_parse(const char *iban, lk_iban_info *out);

#endif
