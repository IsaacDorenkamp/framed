import math
import typing



def distribute(amount: int, weights: typing.Sequence[int]) -> list[int]:
    if amount < 1:
        raise ValueError("Must have at least one unit to distribute!")
    num_weights = len(weights)
    total_weight = sum(weights)
    if total_weight == 0:
        result = [1 for _ in range(num_weights)]
        consumed = sum(result)
    else:
        result = [max(1, math.floor(amount * (weight / total_weight))) for weight in weights]
        consumed = sum(result)
        while consumed < amount:
            for slot in range(num_weights):
                if weights[slot] > 0:
                    result[slot] += 1
                    consumed += 1
                    if consumed == amount:
                        break

    while consumed > amount:
        for slot in range(num_weights):
            if (
                total_weight == 0 or weights[slot] > 0
            ) and result[slot] > 0:
                result[slot] -= 1
                consumed -= 1
                if consumed == amount:
                    break

    return result

