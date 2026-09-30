from __future__ import annotations

from typing import Any, Callable, Iterable


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
        from runnable_sequence import RunnableSequence

        return RunnableSequence([self, other])

    def __ror__(self, other: Any) -> "RunnableSequence":
        from runnable_sequence import RunnableSequence

        return RunnableSequence([other, self])


class RunnableLambda(Runnable):
    """Wrap a plain callable as a runnable."""

    def __init__(self, func: Callable[[Any], Any]):
        self.func = func

    def invoke(self, value: Any) -> Any:
        return self.func(value)


class RunnableParallel(Runnable):
    """Run multiple branches in parallel and collect their outputs."""

    def __init__(self, mapping: dict[str, Any] | None = None, **kwargs: Any):
        merged = {}
        if mapping is not None:
            merged.update(mapping)
        merged.update(kwargs)
        self.runnables: dict[str, Any] = merged

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "RunnableParallel":
        return cls(mapping)

    def invoke(self, value: Any) -> dict[str, Any]:
        outputs: dict[str, Any] = {}
        for name, runnable in self.runnables.items():
            if isinstance(value, dict) and name in value:
                branch_input = value[name]
            else:
                branch_input = value
            outputs[name] = _call_step(runnable, branch_input)
        return outputs

    def batch(self, inputs: Iterable[Any]) -> list[dict[str, Any]]:
        return [self.invoke(item) for item in inputs]

    def __or__(self, other: Any) -> "RunnableSequence":
        from runnable_sequence import RunnableSequence

        return RunnableSequence([self, other])


__all__ = ["Runnable", "RunnableLambda", "RunnableParallel"]
