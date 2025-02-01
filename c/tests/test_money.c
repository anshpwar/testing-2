#include <stdint.h>
#include <string.h>

#include "check.h"
#include "lk_money.h"

static lk_money eur(int64_t minor) {
    lk_money m;
    int rc = lk_money_make(&m, minor, 2, "EUR");
    CHECK_EQ(rc, LK_OK);
    return m;
}

int main(void) {
    lk_money a = eur(1050);
    lk_money b = eur(295);
    lk_money out;
    int32_t cmp = 7;

    /* layout */
    CHECK_EQ(lk_money_sizeof(), sizeof(lk_money));
    CHECK_EQ(lk_money_sizeof(), 24);
    CHECK_EQ(a.flags, 0);

    /* construction */
    CHECK_EQ(lk_money_make(&out, 1, 2, "eur"), LK_ERR_CURRENCY);
    CHECK_EQ(lk_money_make(&out, 1, 2, "EURO"), LK_ERR_CURRENCY);
    CHECK_EQ(lk_money_make(&out, 1, 9, "EUR"), LK_ERR_ARG);
    CHECK_EQ(lk_money_make(NULL, 1, 2, "EUR"), LK_ERR_ARG);

    /* add and subtract */
    CHECK_EQ(lk_money_add(&a, &b, &out), LK_OK);
    CHECK_EQ(out.minor, 1345);
    CHECK_EQ(out.exponent, 2);
    CHECK(strcmp(out.currency, "EUR") == 0);
    CHECK_EQ(lk_money_sub(&b, &a, &out), LK_OK);
    CHECK_EQ(out.minor, -755);

    /* currency and exponent must match */
    lk_money usd;
    lk_money_make(&usd, 5, 2, "USD");
    CHECK_EQ(lk_money_add(&a, &usd, &out), LK_ERR_CURRENCY);
    lk_money yen;
    lk_money_make(&yen, 5, 0, "EUR");
    CHECK_EQ(lk_money_add(&a, &yen, &out), LK_ERR_CURRENCY);

    /* overflow is reported, never wrapped */
    lk_money big = eur(INT64_MAX);
    CHECK_EQ(lk_money_add(&big, &b, &out), LK_ERR_OVERFLOW);
    lk_money low = eur(INT64_MIN);
    CHECK_EQ(lk_money_sub(&b, &low, &out), LK_ERR_OVERFLOW);
    CHECK_EQ(lk_money_sub(&low, &b, &out), LK_ERR_OVERFLOW);
    CHECK_EQ(lk_money_mul_int(&big, 2, &out), LK_ERR_OVERFLOW);

    /* multiply by an integer */
    CHECK_EQ(lk_money_mul_int(&a, -3, &out), LK_OK);
    CHECK_EQ(out.minor, -3150);

    /* basis point percentages */
    CHECK_EQ(lk_money_percent_bp(&a, 250, LK_ROUND_HALF_UP, &out), LK_OK);
    CHECK_EQ(out.minor, 26);
    CHECK_EQ(lk_money_percent_bp(&a, 250, LK_ROUND_DOWN, &out), LK_OK);
    CHECK_EQ(out.minor, 26);
    CHECK_EQ(lk_money_percent_bp(&b, 50, LK_ROUND_UP, &out), LK_OK);
    CHECK_EQ(out.minor, 2);
    CHECK_EQ(lk_money_percent_bp(&big, 20000, LK_ROUND_DOWN, &out), LK_ERR_OVERFLOW);

    /* comparison */
    CHECK_EQ(lk_money_cmp(&a, &b, &cmp), LK_OK);
    CHECK_EQ(cmp, 1);
    CHECK_EQ(lk_money_cmp(&b, &a, &cmp), LK_OK);
    CHECK_EQ(cmp, -1);
    CHECK_EQ(lk_money_cmp(&a, &a, &cmp), LK_OK);
    CHECK_EQ(cmp, 0);
    CHECK_EQ(lk_money_cmp(&a, &usd, &cmp), LK_ERR_CURRENCY);

    /* conversion: 10.50 EUR at 1.084500 -> USD, then into a zero-decimal currency */
    CHECK_EQ(lk_money_convert(&a, 1084500, "USD", 2, LK_ROUND_HALF_UP, &out), LK_OK);
    CHECK_EQ(out.minor, 1139);
    CHECK(strcmp(out.currency, "USD") == 0);
    CHECK_EQ(lk_money_convert(&a, 160250000, "JPY", 0, LK_ROUND_HALF_EVEN, &out), LK_OK);
    CHECK_EQ(out.minor, 1683);
    CHECK_EQ(out.exponent, 0);
    CHECK_EQ(lk_money_convert(&a, 1000000, "KWD", 3, LK_ROUND_DOWN, &out), LK_OK);
    CHECK_EQ(out.minor, 10500);
    CHECK_EQ(lk_money_convert(&a, 0, "USD", 2, LK_ROUND_DOWN, &out), LK_ERR_ARG);
    CHECK_EQ(lk_money_convert(&big, 2000000, "USD", 2, LK_ROUND_DOWN, &out), LK_ERR_OVERFLOW);

    /* proportional fee helper */
    CHECK_EQ(lk_fee_minor(10000, LK_ROUND_HALF_UP, 250), 250);
    CHECK_EQ(lk_fee_minor(1999, LK_ROUND_HALF_UP, 150), 30);
    CHECK_EQ(lk_fee_minor(1999, LK_ROUND_DOWN, 150), 29);
    CHECK_EQ(lk_fee_minor(1999, 42, 150), LK_ERR_MODE);
    CHECK_EQ(lk_fee_minor(-1, LK_ROUND_HALF_UP, 150), LK_ERR_ARG);
    CHECK_EQ(lk_fee_minor(INT64_MAX, LK_ROUND_HALF_UP, 2), LK_ERR_OVERFLOW);

    CHECK_DONE();
}
