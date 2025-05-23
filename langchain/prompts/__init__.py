class PromptTemplate:
    def __init__(self, template, input_variables=None):
        self.template = template
        self.input_variables = input_variables or []
    def format(self, **kwargs):
        return self.template.format(**kwargs)
    def __or__(self, other):
        class Chain:
            def __init__(self, template, model):
                self.template = template
                self.model = model
            def invoke(self, variables):
                return self.model.invoke(self.template.format(**variables))
        return Chain(self, other)
