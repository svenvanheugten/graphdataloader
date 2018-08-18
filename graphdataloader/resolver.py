from asyncio import get_event_loop, ensure_future


def resolver(batch_load_fn_retriever):
    class Descriptor:
        def __init__(self):
            self.__futures = {}

        def __set_name__(self, owner, name):
            self.name = name

        def __get__(self, obj, objtype):
            if obj is None:
                return self
            batch_load_fn = batch_load_fn_retriever(obj.__class__)
            if not hasattr(objtype, '_queues'):
                objtype._queues = {}
            if batch_load_fn not in objtype._queues:
                objtype._queues[batch_load_fn] = {}
            queue = objtype._queues[batch_load_fn]

            async def dispatch_queue():
                old_queue = dict(queue)
                queue.clear()
                await batch_load_fn(old_queue)

            def resolve(value):
                if obj not in self.__futures:
                    self.__futures[obj] = get_event_loop().create_future()
                future = self.__futures[obj]
                if not future.done():
                    if isinstance(value, Exception):
                        future.set_exception(value)
                    else:
                        future.set_result(value)

            def fn(*args, **kwargs):
                queue_was_empty = len(queue) == 0
                if obj not in self.__futures:
                    self.__futures[obj] = get_event_loop().create_future()
                    queue.setdefault(obj, set()).add(self.name)
                    if queue_was_empty:
                        get_event_loop().call_soon(
                            ensure_future,
                            dispatch_queue()
                        )
                return self.__futures[obj]
            fn.resolve = resolve
            return fn

        def __repr__(self):
            return self.name

    return Descriptor()
