def summarize_results(results: list[dict]) -> dict:
    total = len(results)
    acceptable = sum(1 for item in results if item.get("acceptable"))
    return {
        "total_cases": total,
        "acceptable_results": acceptable,
        "acceptable_rate": acceptable / total if total else 0,
    }
