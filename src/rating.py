import math

from perf import positivize

G_INFINITY = math.sqrt(0.81 / 0.19) / 9.0

def correction(count):
    """参加回数 count による補正値を返す。"""
    numerator = math.sqrt(sum(0.81**i for i in range(1, count + 1)))
    denominator = sum(0.9**i for i in range(1, count + 1))
    g = numerator / denominator
    return 1200.0 * (g - G_INFINITY) / (1.0 - G_INFINITY)

def rating_from_performances(performances):
    """新しい順に並んだ perf のリストからレートを求める。"""
    numerator = 0.0
    denumerator = 0.0

    for index, performance in enumerate(performances, start=1):
        weight = 0.9**index
        numerator += weight * 2.0 ** (performance / 800.0)
        denumerator += weight

    raw = 800.0 * math.log2(numerator / denumerator)
    return round(positivize(raw - correction(len(performances))))

def predict_new_rating(history, raw_performance):
    """今回の perf を加えたときの（今のレート, 新しいレート）を返す。"""
    rated = [entry for entry in history if entry['IsRated']]

    past = [entry["InnerPerformance"] for entry in reversed(rated)]
    new_rating = rating_from_performances([raw_performance] + past)

    old_rating = rated[-1]["NewRating"] if rated else 0
    return old_rating, new_rating