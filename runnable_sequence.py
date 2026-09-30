from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator


def _call_step(step: Any, value: Any) -> Any:
    if hasattr(step, "invoke"):
        return step.invoke(value)
    if callable(step):
        return step(value)
    raise TypeError(f"Unsupported step {step!r}; expected a callable or runnable.")


class Runnable:
    """Minimal runnable protocol used by the project."""

    def invoke(self, value: Any) -> Any:
        raise NotImplementedError

    def __call__(self, value: Any) -> Any:
        return self.invoke(value)

    def __or__(self, other: Any) -> "RunnableSequence":
        return RunnableSequence([self, other])

    def __ror__(self, other: Any) -> "RunnableSequence":
        return RunnableSequence([other, self])


class RunnableLambda(Runnable):
    """Wrap a plain callable as a runnable."""

    def __init__(self, func: Callable[[Any], Any]):
        self.func = func

    def invoke(self, value: Any) -> Any:
        return self.func(value)


class RunnableSequence(Runnable):
    """Run a list of callables or runnables in order."""

    def __init__(self, steps: Iterable[Any] | None = None):
        self.steps: list[Any] = list(steps) if steps is not None else []

    def append(self, step: Any) -> None:
        self.steps.append(step)

    def extend(self, steps: Iterable[Any]) -> None:
        self.steps.extend(steps)

    def invoke(self, value: Any) -> Any:
        current = value
        for step in self.steps:
            current = _call_step(step, current)
        return current

    def batch(self, inputs: Iterable[Any]) -> list[Any]:
        return [self.invoke(item) for item in inputs]

    def __iter__(self) -> Iterator[Any]:
        return iter(self.steps)

    def __len__(self) -> int:
        return len(self.steps)

    def __or__(self, other: Any) -> "RunnableSequence":
        sequence = RunnableSequence(self.steps)
        sequence.append(other)
        return sequence

    def __ror__(self, other: Any) -> "RunnableSequence":
        sequence = RunnableSequence([other])
        sequence.extend(self.steps)
        return sequence


__all__ = ["Runnable", "RunnableLambda", "RunnableSequence"]
