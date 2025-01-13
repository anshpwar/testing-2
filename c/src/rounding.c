#include "lk_money.h"

static uint64_t magnitude(int64_t v) {
    return v < 0 ? (uint64_t)0 - (uint64_t)v : (uint64_t)v;
}

int lk_add_checked(int64_t a, int64_t b, int64_t *out) {
    if ((b > 0 && a > INT64_MAX - b) || (b < 0 && a < INT64_MIN - b)) {
        return LK_ERR_OVERFLOW;
    }
    *out = a + b;
    return LK_OK;
}

int lk_mul_checked(int64_t a, int64_t b, int64_t *out) {
    if (a == 0 || b == 0) {
        *out = 0;
        return LK_OK;
    }
    if ((a == -1 && b == INT64_MIN) || (b == -1 && a == INT64_MIN)) {
        return LK_ERR_OVERFLOW;
    }
    if (a > 0) {
        if (b > 0 ? a > INT64_MAX / b : b < INT64_MIN / a) {
            return LK_ERR_OVERFLOW;
        }
    } else {
        if (b > 0 ? a < INT64_MIN / b : a != -1 && b < INT64_MAX / a) {
            return LK_ERR_OVERFLOW;
        }
    }
    *out = a * b;
    return LK_OK;
}

int lk_round_div(int64_t num, int64_t den, int32_t mode, int64_t *out) {
    if (den == 0) {
        return LK_ERR_DIV_ZERO;
    }
    if (mode < LK_ROUND_HALF_UP || mode > LK_ROUND_UP) {
        return LK_ERR_MODE;
    }
    int negative = (num < 0) != (den < 0);
    uint64_t un = magnitude(num);
    uint64_t ud = magnitude(den);
    uint64_t q = un / ud;
    uint64_t r = un % ud;
    int bump = 0;
    if (r != 0) {
        switch (mode) {
        case LK_ROUND_DOWN:
            bump = 0;
            break;
        case LK_ROUND_UP:
            bump = 1;
            break;
        case LK_ROUND_HALF_UP:
            bump = r >= ud - r;
            break;
        default: /* LK_ROUND_HALF_EVEN */
            bump = r > ud - r || (r == ud - r && (q & 1u));
            break;
        }
    }
    q += (uint64_t)bump;
    uint64_t limit = negative ? (uint64_t)INT64_MAX + 1u : (uint64_t)INT64_MAX;
    if (q > limit) {
        return LK_ERR_OVERFLOW;
    }
    *out = negative ? (int64_t)((uint64_t)0 - q) : (int64_t)q;
    return LK_OK;
}
