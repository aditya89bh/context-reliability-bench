from __future__ import annotations

from context_reliability_bench.categories.base import BenchmarkCategory


class CategoryRegistry:
    def __init__(self) -> None:
        self._categories: dict[str, BenchmarkCategory] = {}

    def register(self, category: BenchmarkCategory) -> None:
        if category.name in self._categories:
            raise ValueError(
                f"Category '{category.name}' is already registered."
            )
        self._categories[category.name] = category

    def get(self, name: str) -> BenchmarkCategory:
        if name not in self._categories:
            raise KeyError(f"Category '{name}' not found in registry.")
        return self._categories[name]

    def names(self) -> list[str]:
        return sorted(self._categories)

    def categories(self) -> list[BenchmarkCategory]:
        return [self._categories[n] for n in sorted(self._categories)]

    def __len__(self) -> int:
        return len(self._categories)

    def __contains__(self, name: object) -> bool:
        return name in self._categories
