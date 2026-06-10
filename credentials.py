import hashlib
from faker import Faker

fake = Faker()

def generate_credentials() -> tuple[str, str]:
    username = fake.user_name()[3:32]
    password = hashlib.md5(username.lower().encode()).hexdigest()
    return username, password
