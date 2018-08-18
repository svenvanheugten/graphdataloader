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

    title = resolver()
    author = resolver()

    @classmethod
    async def batch_load_fn(cls, obj_to_attr_names):
        documents = await get_blogs(
            {obj.id for obj in obj_to_attr_names},
            include_titles=any('title' in attr_names for attr_names in obj_to_attr_names.values()),
            include_authors=any('author' in attr_names for attr_names in obj_to_attr_names.values())
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

    name = resolver()
    rating = resolver()

    @classmethod
    async def batch_load_fn(cls, obj_to_attr_names):
        documents = await get_authors({obj.id for obj in obj_to_attr_names})
        for document in documents:
            author = cls(document['id'])
            author.name.resolve(document['name'])
            author.rating.resolve(document['rating'])

    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
```

Now, resolving a `Blog`'s author and then resolving the author's name does just one request! Only if you also resolve the author's rating, a second request goes out.
