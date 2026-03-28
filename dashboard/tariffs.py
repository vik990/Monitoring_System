from django.conf import settings


def get_tariff_blocks():
    """Return Mauritius tariff blocks as (upper_kwh_limit, rate_mur_per_kwh)."""
    return getattr(
        settings,
        'MAURITIUS_TARIFF_BLOCKS',
        [
            (50, 3.50),
            (100, 5.00),
            (200, 6.50),
            (float('inf'), 8.00),
        ],
    )


def calculate_tariff_cost(kwh: float) -> float:
    """Calculate block/slab tariff cost for given kWh."""
    units_left = max(float(kwh or 0), 0.0)
    if units_left == 0:
        return 0.0

    cost = 0.0
    prev_limit = 0.0
    for upper_limit, rate in get_tariff_blocks():
        block_span = float(upper_limit) - prev_limit
        if units_left <= 0:
            break
        take = min(units_left, block_span)
        cost += take * float(rate)
        units_left -= take
        prev_limit = float(upper_limit)
    return round(cost, 2)


def get_marginal_rate(current_kwh: float) -> float:
    """Rate that applies for the next 1 kWh at current usage level."""
    kwh = max(float(current_kwh or 0), 0.0)
    for upper_limit, rate in get_tariff_blocks():
        if kwh < float(upper_limit):
            return float(rate)
    return float(get_tariff_blocks()[-1][1])
