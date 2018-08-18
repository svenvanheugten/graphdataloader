import asynctest
import asyncio

from graphdataloader import resolver


class TestResolver(asynctest.TestCase):
    async def test(self):
        class Test:
            call_count = 0

            def __init__(self, id):
                self.id = id

            resolve_name = resolver(lambda cls: cls.batch_load_fn)
            resolve_description = resolver(lambda cls: cls.batch_load_fn)

            @classmethod
            async def batch_load_fn(cls, obj_to_resolver_names):
                cls.call_count += 1
                for obj, resolver_names in obj_to_resolver_names.items():
                    if 'resolve_name' in resolver_names:
                        obj.resolve_name.give('Post ' + str(obj.id))
                    if 'resolve_description' in resolver_names:
                        obj.resolve_description.give('About ' + str(obj.id))

            def __eq__(self, other):
                return self.id == other.id

            def __hash__(self):
                return hash(self.id)

        async def verify(obj):
            self.assertEqual(
                await obj.resolve_name(),
                'Post ' + str(obj.id)
            )
            self.assertEqual(
                await obj.resolve_description(), 'About ' + str(obj.id)
            )

        await asyncio.gather(verify(Test(0)), verify(Test(1)))

        self.assertEqual(Test.call_count, 2)
