def cond_test(a):
    x = 0
    if a > 0 and a < 5:
        x = 1
 
    b = a + 1
    if x == 1 and b > 6:
        return 15
    return b

def type_test():
    a = 1
    b = a
    c = b
    d = 'a'
    e = d
    f = e
    f = c
    return f

def basic_cond(x):
    if x > 5:
        x = 2
    return x

def basic_str():
    return 'abc'

def true_cond(x):
    x = 1
    if x > 5 or x == 2:
        x = 2
    return x

def single_block():
    b = 12
    c = b
    return c

def print_leak(x):
    print(x)
    return x

def print_test(x):
    if x < 200:
        print('error')
    else:
        print('print')
    print('last')
    return 5

def concrete_print_test(x):
    if x % 2 == 0:
        print('error')
    else:
        print('print')
    print('last')
    return 5

def concrete_errors_test(x):
    if x % 2 == 0:
        ValueError('error')
    else:
        ValueError('print')
    ValueError('last')
    return 5

def math_block(d):
    # d = 9
    d = 3 * d
    b = 2
    if d < 10:
        b = d - b
        c = b + b
    else:
        c = 10
    c = c
    c = c * 5 + 5
    return c / 5

def basic_concrete(x):
    if x > 1024 or x < -1023:
        return -1
    if x <= 0:
        w = 2
    else:
        parity = x % 2
        if parity == 0:
            w = 2
        else:
            if x > 512:
                return 2
            else:
                w = 3
    return w

def loop_test(x): # TODO: Implement pop_jump_backward
    while x < 50:
        x += 5
    return x

def register_user(username, age):
    if not username.isalnum():
        raise ValueError("Username must be alphanumeric")
    if not isinstance(age, int) or age < 18 or age > 99:
        raise ValueError("Age must be an integer between 18 and 99")
    
    # Registration logic would go here
    print(f"Registering user: {username} with age {age}")

def multi_error():
    # Usage
    try:
        register_user("user123", 25)
        register_user("user-abc", 30)  # This will raise an error
        register_user("user456", "20")  # This will raise an error
    except ValueError as e:
        print("Error:", e)

def no_call_error():
    try:
        age = 16
        if age < 20:
            raise ValueError("Username must be alphanumeric")
        if age > 99:
            raise ValueError("Age must be an integer between 18 and 99")
    
        # Registration logic would go here
        print(f"Registering user: With age {age}")
    except ValueError as e:
        print("Error:", e)

if __name__ == '__main__':
    print(f"Out: {cond_test(3)}")