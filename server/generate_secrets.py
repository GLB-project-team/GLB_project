import secrets

secret_key = secrets.token_hex(16)  # 32자리 16진수 키 생성
print(secret_key)