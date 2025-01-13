#include <string.h>

#include "lk_money.h"

size_t lk_money_sizeof(void) {
    return sizeof(lk_money);
}

int lk_currency_valid(const char *currency) {
    if (currency == NULL || strlen(currency) != 3) {
        return 0;
    }
    for (int i = 0; i < 3; i++) {
        if (currency[i] < 'A' || currency[i] > 'Z') {
            return 0;
        }
    }
    return 1;
}

static int pow10_checked(int32_t n, int64_t *out) {
    int64_t v = 1;
    if (n < 0 || n > 18) {
        return LK_ERR_ARG;
    }
    for (int32_t i = 0; i < n; i++) {
        v *= 10;
    }
    *out = v;
    return LK_OK;
}

int lk_money_make(lk_money *out, int64_t minor, int32_t exponent, const char *currency) {
    if (out == NULL || exponent < 0 || exponent > LK_MAX_EXPONENT) {
        return LK_ERR_ARG;
    }
    if (!lk_currency_valid(currency)) {
        return LK_ERR_CURRENCY;
    }
    memset(out, 0, sizeof(*out));
    out->minor = minor;
    out->exponent = exponent;
    memcpy(out->currency, currency, 3);
    return LK_OK;
}

static int same_unit(const lk_money *a, const lk_money *b) {
    if (a == NULL || b == NULL) {
        return LK_ERR_ARG;
    }
    if (memcmp(a->currency, b->currency, 4) != 0 || a->exponent != b->exponent) {
        return LK_ERR_CURRENCY;
    }
    return LK_OK;
}

static int combine(const lk_money *a, const lk_money *b, int64_t minor, lk_money *out) {
    lk_money tmp;
    memset(&tmp, 0, sizeof(tmp));
    tmp.minor = minor;
    tmp.exponent = a->exponent;
    memcpy(tmp.currency, a->currency, 4);
    (void)b;
    *out = tmp;
    return LK_OK;
}

int lk_money_add(const lk_money *a, const lk_money *b, lk_money *out) {
    int rc = same_unit(a, b);
    int64_t sum;
    if (rc != LK_OK || out == NULL) {
        return rc != LK_OK ? rc : LK_ERR_ARG;
    }
    rc = lk_add_checked(a->minor, b->minor, &sum);
    return rc != LK_OK ? rc : combine(a, b, sum, out);
}

int lk_money_sub(const lk_money *a, const lk_money *b, lk_money *out) {
    int rc = same_unit(a, b);
    int64_t diff;
    if (rc != LK_OK || out == NULL) {
        return rc != LK_OK ? rc : LK_ERR_ARG;
    }
    if (b->minor == INT64_MIN) {
        return LK_ERR_OVERFLOW;
    }
    rc = lk_add_checked(a->minor, -b->minor, &diff);
    return rc != LK_OK ? rc : combine(a, b, diff, out);
}

int lk_money_mul_int(const lk_money *a, int64_t k, lk_money *out) {
    int64_t prod;
    int rc;
    if (a == NULL || out == NULL) {
        return LK_ERR_ARG;
    }
    rc = lk_mul_checked(a->minor, k, &prod);
    return rc != LK_OK ? rc : combine(a, a, prod, out);
}

int lk_money_percent_bp(const lk_money *a, int32_t bp, int32_t mode, lk_money *out) {
    int64_t scaled;
    int64_t result;
    int rc;
    if (a == NULL || out == NULL) {
        return LK_ERR_ARG;
    }
    rc = lk_mul_checked(a->minor, bp, &scaled);
    if (rc != LK_OK) {
        return rc;
    }
    rc = lk_round_div(scaled, 10000, mode, &result);
    return rc != LK_OK ? rc : combine(a, a, result, out);
}

int lk_money_cmp(const lk_money *a, const lk_money *b, int32_t *result) {
    int rc = same_unit(a, b);
    if (rc != LK_OK || result == NULL) {
        return rc != LK_OK ? rc : LK_ERR_ARG;
    }
    *result = a->minor < b->minor ? -1 : (a->minor > b->minor ? 1 : 0);
    return LK_OK;
}

int lk_money_convert(const lk_money *a, int64_t rate_micro, const char *to_currency, int32_t to_exponent,
                     int32_t mode, lk_money *out) {
    int64_t num;
    int64_t den = 1000000;
    int64_t scale = 1;
    int64_t result;
    int32_t delta;
    int rc;
    if (a == NULL || out == NULL || rate_micro <= 0 || to_exponent < 0 || to_exponent > LK_MAX_EXPONENT) {
        return LK_ERR_ARG;
    }
    if (!lk_currency_valid(to_currency)) {
        return LK_ERR_CURRENCY;
    }
    rc = lk_mul_checked(a->minor, rate_micro, &num);
    if (rc != LK_OK) {
        return rc;
    }
    delta = to_exponent - a->exponent;
    if (delta >= 0) {
        (void)pow10_checked(delta, &scale);
        rc = lk_mul_checked(num, scale, &num);
        if (rc != LK_OK) {
            return rc;
        }
    } else {
        (void)pow10_checked(-delta, &scale);
        den *= scale;
    }
    rc = lk_round_div(num, den, mode, &result);
    if (rc != LK_OK) {
        return rc;
    }
    return lk_money_make(out, result, to_exponent, to_currency);
}

int64_t lk_fee_minor(int64_t minor, int32_t bp) {
    int64_t scaled;
    int64_t fee;
    int rc;
    if (minor < 0 || bp < 0) {
        return LK_ERR_ARG;
    }
    rc = lk_mul_checked(minor, bp, &scaled);
    if (rc != LK_OK) {
        return rc;
    }
    rc = lk_round_div(scaled, 10000, LK_ROUND_HALF_UP, &fee);
    return rc != LK_OK ? rc : fee;
}
