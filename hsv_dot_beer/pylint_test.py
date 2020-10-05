from functools import wraps


def my_decorator(some_arg):
    def inner_callable(func):
        @wraps(func)
        def inner(*args, **kwargs):
            print(some_arg)
            return func(some_arg, *args, **kwargs)

        return inner

    return inner_callable


class MyTestClass:
    MY_CONSTANT = [1, 2, 3]

    @my_decorator(MY_CONSTANT)
    def test_func(self, some_arg, *args, **kwargs):
        print("wee", self, some_arg, args, kwargs)


MyTestClass().test_func("poo")
