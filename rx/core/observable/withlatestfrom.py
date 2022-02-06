from typing import Any, List, Optional, Tuple

from rx.core import Observable, abc
from rx.disposable import CompositeDisposable, SingleAssignmentDisposable
from rx.internal.utils import NotSet


def with_latest_from_(
    parent: Observable[Any], *sources: Observable[Any]
) -> Observable[Tuple[Any, ...]]:
    NO_VALUE = NotSet()

    def subscribe(
        observer: abc.ObserverBase[Any], scheduler: Optional[abc.SchedulerBase] = None
    ) -> abc.DisposableBase:
        def subscribe_all(
            parent: Observable[Any], *children: Observable[Any]
        ) -> List[SingleAssignmentDisposable]:

            values = [NO_VALUE for _ in children]

            def subscribe_child(i: int, child: Observable[Any]):
                subscription = SingleAssignmentDisposable()

                def on_next(value: Any) -> None:
                    with parent.lock:
                        values[i] = value

                subscription.disposable = child.subscribe_(
                    on_next, observer.on_error, scheduler=scheduler
                )
                return subscription

            parent_subscription = SingleAssignmentDisposable()

            def on_next(value: Any) -> None:
                with parent.lock:
                    if NO_VALUE not in values:
                        result = (value,) + tuple(values)
                        observer.on_next(result)

            disp = parent.subscribe_(
                on_next, observer.on_error, observer.on_completed, scheduler
            )
            parent_subscription.disposable = disp

            children_subscription = [
                subscribe_child(i, child) for i, child in enumerate(children)
            ]

            return [parent_subscription] + children_subscription

        return CompositeDisposable(subscribe_all(parent, *sources))

    return Observable(subscribe)


__all__ = ["with_latest_from_"]
