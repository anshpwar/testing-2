#ifndef LK_MONEY_H
#define LK_MONEY_H

#include <stddef.h>
#include <stdint.h>

/* Status codes shared by every lk_* function. Zero is success. */
#define LK_OK 0
#define LK_ERR_OVERFLOW (-1)
#define LK_ERR_DIV_ZERO (-2)
#define LK_ERR_CURRENCY (-3)
#define LK_ERR_ARG (-4)
#define LK_ERR_MODE (-5)
#define LK_ERR_IBAN_FORMAT (-6)
#define LK_ERR_IBAN_COUNTRY (-7)
#define LK_ERR_IBAN_LENGTH (-8)
#define LK_ERR_IBAN_CHECK (-9)

/* Rounding modes. */
#define LK_ROUND_HALF_UP 0
#define LK_ROUND_HALF_EVEN 1
#define LK_ROUND_DOWN 2
#define LK_ROUND_UP 3

#define LK_MAX_EXPONENT 6

/* Fixed-point amount: `minor` units of 10^-exponent of `currency`. */
typedef struct lk_money {
    int64_t minor;
    int32_t exponent;
    char currency[4];
    uint32_t flags;
} lk_money;

size_t lk_money_sizeof(void);

/* Rounded integer division num / den under `mode`. */
int lk_round_div(int64_t num, int64_t den, int32_t mode, int64_t *out);

/* Overflow-checked primitives. */
int lk_add_checked(int64_t a, int64_t b, int64_t *out);
int lk_mul_checked(int64_t a, int64_t b, int64_t *out);

int lk_currency_valid(const char *currency);

int lk_money_make(lk_money *out, int64_t minor, int32_t exponent, const char *currency);
int lk_money_add(const lk_money *a, const lk_money *b, lk_money *out);
int lk_money_sub(const lk_money *a, const lk_money *b, lk_money *out);
int lk_money_mul_int(const lk_money *a, int64_t k, lk_money *out);
int lk_money_percent_bp(const lk_money *a, int32_t bp, int32_t mode, lk_money *out);
int lk_money_cmp(const lk_money *a, const lk_money *b, int32_t *result);
int lk_money_convert(const lk_money *a, int64_t rate_micro, const char *to_currency, int32_t to_exponent,
                     int32_t mode, lk_money *out);

/* Proportional fee: minor * bp / 10000 under `mode`. Negative result is a status code. */
int64_t lk_fee_minor(int64_t minor, int32_t mode, int32_t bp);

#endif
