def cond_test(a):
    x = 0
    if a > 0 and a < 5:
        x = 1
 
    b = a + 1
    if x == 1 and b > 6:
        return 15
    return b

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

def math_block():
    d = 9
    d = 3 * d
    b = 2
    b = d - b
    c = b + b
    c = c
    c = c * 5 + 5
    return c / 5

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
    no_call_error()