class Book():
    class Chapter():
        def __init__(self, heading, content):
            self.heading = heading
            self.content = content

    def __init__(self):
        self.title: str
        self.author: str
        self.chapters = []
    
    def read(self):
        print('======START======')
        print(self.title)
        print(self.author)
        for item in self.chapters:
            print(item.heading)
            print(item.content)
        print('======FIN======')