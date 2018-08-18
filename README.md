graphdataloader
===============
This gives DataLoader a natural place in your object graph. It is based on [aiodataloader](https://github.com/syrusakbary/aiodataloader).

Example
-------
Suppose you have a `Blog`-class and an `Author`-class. For modularity, each have their own property resolvers. However, when you request a blog's author, the API call doesn't just return the `id`, but also some other information, which you don't want to go to waste. So you do this:

```python
class Blog:
    def __init__(self, id):
        self.id = id

    resolve_title = resolver(lambda cls: cls.batch_load_fn)
    resolve_author = resolver(lambda cls: cls.batch_load_fn)

    @classmethod
    async def batch_load_fn(cls, obj_to_resolver_names):
        documents = await get_blogs(
            {obj.id for obj in obj_to_resolver_names},
            include_titles=any('resolve_title' in resolver_names for resolver_names in obj_to_resolver_names.values()),
            include_authors=any('resolve_author' in resolver_names for resolver_names in obj_to_resolver_names.values())
        )
        for document in documents:
            blog = cls(document['id'])
            if 'title' in document:
                blog.resolve_title.give(document['title'])
            if 'author' in document:
                author = Author(document['author']['id'])
                author.resolve_name.give(document['author']['name'])
                blog.resolve_author.give(author)

    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)


class Author:
    def __init__(self, id):
        self.id = id

    resolve_name = resolver(lambda cls: cls.batch_load_fn)
    resolve_rating = resolver(lambda cls: cls.batch_load_fn)

    @classmethod
    async def batch_load_fn(cls, obj_to_resolver_names):
        documents = await get_authors({obj.id for obj in obj_to_resolver_names})
        for document in documents:
            author = cls(document['id'])
            author.resolve_name.give(document['name'])
            author.resolve_rating.give(document['rating'])

    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
```

Now, resolving a `Blog`'s author and then resolving the author's name does just one request! Only if you also resolve the author's rating, a second request goes out.
