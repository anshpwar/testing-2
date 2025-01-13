#include <string.h>

#include "lk_iban.h"

typedef struct {
    const char *country;
    int length;
} iban_length;

/* Registered lengths for the countries this ledger settles with. */
static const iban_length LENGTHS[] = {
    {"AT", 20}, {"BE", 16}, {"CH", 21}, {"DE", 22}, {"ES", 24}, {"FR", 27}, {"GB", 22},
    {"IE", 22}, {"IT", 27}, {"LU", 20}, {"NL", 18}, {"PL", 28}, {"PT", 25}, {"SE", 24},
};

size_t lk_iban_info_sizeof(void) {
    return sizeof(lk_iban_info);
}

static int is_upper(char c) {
    return c >= 'A' && c <= 'Z';
}

static int is_digit(char c) {
    return c >= '0' && c <= '9';
}

int lk_iban_expected_length(const char *country) {
    if (country == NULL || !is_upper(country[0]) || !is_upper(country[1])) {
        return LK_ERR_IBAN_FORMAT;
    }
    for (size_t i = 0; i < sizeof(LENGTHS) / sizeof(LENGTHS[0]); i++) {
        if (country[0] == LENGTHS[i].country[0] && country[1] == LENGTHS[i].country[1]) {
            return LENGTHS[i].length;
        }
    }
    return LK_ERR_IBAN_COUNTRY;
}

/* Feeds one character of the rearranged string into the running remainder. */
static int feed(int rem, char c) {
    if (is_digit(c)) {
        return (rem * 10 + (c - '0')) % 97;
    }
    if (is_upper(c)) {
        int v = c - 'A' + 10;
        return (rem * 100 + v) % 97;
    }
    return -1;
}

static int mod97_parts(const char *head, size_t head_len, const char *tail, size_t tail_len) {
    int rem = 0;
    for (size_t i = 0; i < tail_len; i++) {
        rem = feed(rem, tail[i]);
        if (rem < 0) {
            return LK_ERR_IBAN_FORMAT;
        }
    }
    for (size_t i = 0; i < head_len; i++) {
        rem = feed(rem, head[i]);
        if (rem < 0) {
            return LK_ERR_IBAN_FORMAT;
        }
    }
    return rem;
}

int lk_iban_mod97(const char *iban) {
    size_t n;
    if (iban == NULL) {
        return LK_ERR_ARG;
    }
    n = strlen(iban);
    if (n < 5 || n > 34) {
        return LK_ERR_IBAN_LENGTH;
    }
    return mod97_parts(iban, 4, iban + 4, n - 4);
}

int lk_iban_validate(const char *iban) {
    size_t n;
    int expected;
    int rem;
    if (iban == NULL) {
        return LK_ERR_ARG;
    }
    n = strlen(iban);
    if (n < 5 || n > 34) {
        return LK_ERR_IBAN_LENGTH;
    }
    if (!is_upper(iban[0]) || !is_upper(iban[1]) || !is_digit(iban[2]) || !is_digit(iban[3])) {
        return LK_ERR_IBAN_FORMAT;
    }
    expected = lk_iban_expected_length(iban);
    if (expected < 0) {
        return expected;
    }
    if ((int)n != expected) {
        return LK_ERR_IBAN_LENGTH;
    }
    rem = lk_iban_mod97(iban);
    if (rem < 0) {
        return rem;
    }
    return rem == 1 ? LK_OK : LK_ERR_IBAN_CHECK;
}

int lk_iban_check_digits(const char *country, const char *bban, char *out) {
    char head[5];
    int rem;
    size_t n;
    if (country == NULL || bban == NULL || out == NULL) {
        return LK_ERR_ARG;
    }
    if (!is_upper(country[0]) || !is_upper(country[1]) || country[2] != '\0') {
        return LK_ERR_IBAN_FORMAT;
    }
    n = strlen(bban);
    if (n == 0 || n > 30) {
        return LK_ERR_IBAN_LENGTH;
    }
    head[0] = country[0];
    head[1] = country[1];
    head[2] = '0';
    head[3] = '0';
    head[4] = '\0';
    rem = mod97_parts(head, 4, bban, n);
    if (rem < 0) {
        return rem;
    }
    out[0] = (char)('0' + (98 - rem) / 10);
    out[1] = (char)('0' + (98 - rem) % 10);
    out[2] = '\0';
    return LK_OK;
}

int lk_iban_parse(const char *iban, lk_iban_info *out) {
    int rc = lk_iban_validate(iban);
    if (out == NULL) {
        return LK_ERR_ARG;
    }
    if (rc != LK_OK) {
        return rc;
    }
    memset(out, 0, sizeof(*out));
    out->country[0] = iban[0];
    out->country[1] = iban[1];
    out->check_digits = (iban[2] - '0') * 10 + (iban[3] - '0');
    out->length = (int32_t)strlen(iban);
    out->expected_length = lk_iban_expected_length(iban);
    return LK_OK;
}
