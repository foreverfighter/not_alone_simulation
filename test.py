def zero():
    print('i am awesome')
    return "zero"


def one():
    return "one"


def numbers_to_functions_to_strings(argument):
    switcher = {
        0: zero,
        1: one,
        2: lambda: "two",
    }
    # Get the function from switcher dictionary
    func = switcher.get(argument, lambda: "nothing")
    # Execute the function
    return func()


numbers_to_functions_to_strings(0)
