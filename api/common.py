from pydantic import BaseModel


def to_camel(string: str) -> str:
    string_split = string.split('_')
    return string_split[0] + ''.join(
        word.capitalize() for word in string_split[1:])


class BaseValidator(BaseModel):
    def json(self, **kwargs):
        kwargs.setdefault('by_alias', True)
        return super().json(**kwargs)

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        orm_mode = True
        extra = 'forbid'
