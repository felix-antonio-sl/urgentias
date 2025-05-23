class PydanticOutputParser:
    def __init__(self, pydantic_object):
        self.pydantic_object = pydantic_object
    def parse(self, text):
        try:
            return self.pydantic_object.model_validate_json(text)
        except Exception:
            return None
