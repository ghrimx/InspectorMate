from utils.decorators import singleton

@singleton
class OnlyOne:
    pass

def test_singleton():
    only_one = OnlyOne()
    another_one = OnlyOne()
    print(f"only_one: {id(only_one)}, another_one: {id(another_one)}")
    assert id(only_one) == id(another_one)