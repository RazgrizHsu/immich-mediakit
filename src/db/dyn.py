from db.sets import lg, get, save

class AutoDbField:
    def __init__(self, key, default=None):
        self.key = key
        self.default = default

    def __get__(self, instance, owner):
        if instance is None: return self
        return get(self.key, self.default)

    def __set__(self, instance, value):
        # lg.info(f"[dynField] Saving setting value: {self.key} = {value}")
        save(self.key, str(value))


class DtoSets:
    usrId = AutoDbField('usrId')
    useType = AutoDbField('useType')
    photoQ = AutoDbField('photoQ')

    @classmethod
    def get(cls, key, default=None):
        value = get(key, default)
        return value

    @classmethod
    def save(cls, key, value):
        return save(key, str(value))


# global
dto = DtoSets()
