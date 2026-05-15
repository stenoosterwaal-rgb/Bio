def calculate_grade(raw_score: int, max_score: int) -> float:
    if max_score <= 0:
        return 1.0
    grade = 1 + 9 * (raw_score / max_score)
    return round(max(1.0, min(10.0, grade)), 1)
