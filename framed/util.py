import math
import typing



def distribute(amount: int, weights: typing.Sequence[int], minimums: typing.Sequence[int] | None = None) -> list[int]:
    if minimums is None:
        minimums = [1] * len(weights)
    if len(minimums) != len(weights):
        raise ValueError("'minimums' must have equal length to weights.")
    if amount < 1:
        raise ValueError("Must have at least one unit to distribute!")
    num_weights = len(weights)
    total_weight = sum(weights)
    if total_weight == 0:
        result = [1 for _ in range(num_weights)]
        consumed = sum(result)
    else:
        result = [max(minimum, math.floor(amount * (weight / total_weight))) for weight, minimum in zip(weights, minimums)]
        consumed = sum(result)
        if total_weight > 0:
            while consumed < amount:
                for slot in range(num_weights):
                    if weights[slot] > 0:
                        result[slot] += 1
                        consumed += 1
                        if consumed == amount:
                            break

    dire = False  # cannot reach "amount" while respecting minimums
    very_dire = False  # dire is true, and still cannot reach "amount." This requires at least some values to be 0.
    while consumed > amount:
        previous = consumed
        for slot in range(num_weights):
            if result[slot] > minimums[slot] or (dire and result[slot] > 1) or (very_dire and result[slot] > 0):
                result[slot] -= 1
                consumed -= 1
                if consumed == amount:
                    break

        was_dire = dire
        dire = previous == consumed
        very_dire = was_dire and dire

    return result

