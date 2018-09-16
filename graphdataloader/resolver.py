from frozendict import frozendict
from asyncio import get_event_loop, ensure_future


class Resolver:
    def __init__(self, get_batch_load_fn, get_setter_fn=None):
        self.__futures = {}
        self.__get_batch_load_fn = get_batch_load_fn
        self.__get_setter_fn = get_setter_fn

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype):
        if obj is None:
            return self

        batch_load_fn = self.__get_batch_load_fn(obj.__class__)

        if not hasattr(objtype, '_queues'):
            objtype._queues = {}
        if batch_load_fn not in objtype._queues:
            objtype._queues[batch_load_fn] = set()
        queue = objtype._queues[batch_load_fn]

        async def dispatch_queue():
            old_queue = set(queue)
            queue.clear()
            await batch_load_fn(old_queue)
            assert all(
                self.__futures[(obj, arguments)].done()
                for obj, attr_name, arguments in old_queue
            ), "Not everything was resolved."

        def do_resolve(identity, value):
            if identity not in self.__futures or self.__futures[identity].done():
                self.__futures[identity] = get_event_loop().create_future()
            future = self.__futures[identity]
            if isinstance(value, Exception):
                future.set_exception(value)
            else:
                future.set_result(value)

        def with_arguments(**kwargs):
            def resolvable():
                pass
            resolvable.resolve = lambda value: do_resolve(
                (obj, frozendict(kwargs)),
                value
            )
            return resolvable

        def fn(**kwargs):
            arguments = frozendict(kwargs)
            identity = (obj, arguments)
            queue_was_empty = len(queue) == 0
            if identity not in self.__futures:
                self.__futures[identity] = get_event_loop().create_future()
                queue.add((obj, self.name, arguments))
                if queue_was_empty:
                    get_event_loop().call_soon(
                        ensure_future,
                        dispatch_queue()
                    )
            return self.__futures[identity]

        fn.with_arguments = with_arguments
        fn.resolve = lambda value: with_arguments().resolve(value)

        if self.__get_setter_fn:
            async def setter(value):
                fn.resolve(value)
                await self.__get_setter_fn(obj)(value)

            fn.set = setter

        return fn

    def __repr__(self):
        return self.name
