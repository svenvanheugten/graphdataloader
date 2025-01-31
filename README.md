graphdataloader
===============
This gives DataLoader a natural place in your object graph. It is based on [aiodataloader](https://github.com/syrusakbary/aiodataloader).

Example
-------
Suppose you have a `Blog`-class and an `Author`-class. For modularity, each have their own property resolvers. However, when you request a blog's author, the API call doesn't just return the `id`, but also some other information, which you don't want going to waste. So you do this:

```python
from graphdataloader import Resolver
from external import get_blogs, get_authors


class Blog:
    def __init__(self, id):
        self.id = id

    title = Resolver()
    author = Resolver()

    @classmethod
    async def batch_load_fn(cls, calls):
        documents = await get_blogs(
            {obj.id for obj, attr_name, args in calls},
            include_titles=any(attr_name == 'title' for obj, attr_name, args in calls.values()),
            include_authors=any(attr_name == 'author' for obj, attr_name, args in calls.values())
        )
        for document in documents:
            blog = cls(document['id'])
            if 'title' in document:
                blog.title.resolve(document['title'])
            if 'author' in document:
                author = Author(document['author']['id'])
                author.name.resolve(document['author']['name'])
                blog.author.resolve(author)

    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)


class Author:
    def __init__(self, id):
        self.id = id

    name = Resolver()
    rating = Resolver()

    @classmethod
    async def batch_load_fn(cls, calls):
        documents = await get_authors({obj.id for obj, attr_name, args in calls})
        for document in documents:
            author = cls(document['id'])
            author.name.resolve(document['name'])
            author.rating.resolve(document['rating'])

    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
```

Now, getting a `Blog`'s author and then getting the author's name does just one request. Only if you also get the author's rating, a second request goes out.

Mutations
---------
If you specify a setter on a `Resolver`, you can use `.set(value)` to update both the cache and call your setter function:

```python
from external import update_post

class Post:
    def __init__(self, id):
        self.id = id

    name = Resolver(lambda cls: cls.batch_load_fn, lambda self: self.__set_name)

    async def __set_name(self, value):
        await update_post(self.id, value)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

post = Post(0)
await post.name.set('New post name')
```
