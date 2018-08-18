import asynctest
import asyncio

from graphdataloader import resolver


class TestResolver(asynctest.TestCase):
    async def test(self):
        class Test:
            call_count = 0

            def __init__(self, id):
                self.id = id

            name = resolver(lambda cls: cls.batch_load_fn)
            description = resolver(lambda cls: cls.batch_load_fn)

            @classmethod
            async def batch_load_fn(cls, obj_to_attr_names):
                cls.call_count += 1
                for obj, attr_names in obj_to_attr_names.items():
                    if 'name' in attr_names:
                        obj.name.resolve('Post ' + str(obj.id))
                    if 'description' in attr_names:
                        obj.description.resolve('About ' + str(obj.id))

            def __eq__(self, other):
                return self.id == other.id

            def __hash__(self):
                return hash(self.id)

        async def verify(obj):
            self.assertEqual(
                await obj.name(),
                'Post ' + str(obj.id)
            )
            self.assertEqual(
                await obj.description(), 'About ' + str(obj.id)
            )

        await asyncio.gather(verify(Test(0)), verify(Test(1)))

        self.assertEqual(Test.call_count, 2)
