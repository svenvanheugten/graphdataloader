import asynctest
import asyncio

from graphdataloader import Resolver


class TestResolver(asynctest.TestCase):
    async def test(self):
        class Post:
            call_count = 0

            def __init__(self, id):
                self.id = id

            name = Resolver(lambda cls: cls.batch_load_fn)
            description = Resolver(lambda cls: cls.batch_load_fn)
            comments = Resolver(lambda cls: cls.batch_load_fn)

            @classmethod
            async def batch_load_fn(cls, calls):
                cls.call_count += 1
                for obj, attr_names, kwargs in calls:
                    if 'name' in attr_names:
                        obj.name.resolve('Post ' + str(obj.id))
                    if 'description' in attr_names:
                        obj.description.resolve('About ' + str(obj.id))
                    if 'comments' in attr_names:
                        obj.comments \
                            .with_arguments(count=kwargs['count']) \
                            .resolve(list(range(kwargs['count'])))

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
            self.assertEqual(
                await obj.comments(count=10), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            )

        await asyncio.gather(verify(Post(0)), verify(Post(1)))

        self.assertEqual(Post.call_count, 3)
