class ChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass
    def invoke(self, prompt):
        class Msg:
            def __init__(self, content=""):
                self.content = content
        return Msg()
