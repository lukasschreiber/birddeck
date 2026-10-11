def profile_folder_id(profile_id: str) -> str:
    clean_id = profile_id.replace('-', '')
    padded = clean_id + "000"
    groups = [padded[i:i+5] for i in range(0, len(padded), 5)]
    converted = []
    
    def int_to_base32(n):
        alphabet = "0123456789abcdefghijklmnopqrstuv"
        if n == 0:
            return "0"
        result = ""
        while n > 0:
            result = alphabet[n % 32] + result
            n //= 32
        return result

    converted = [int_to_base32(int(g, 16)).rjust(4, '0') for g in groups]
    joined = ''.join(converted)
    trimmed = joined[:26]
    remapped = trimmed.upper().replace('V', 'W').replace('U', 'V')
    return remapped + 'Z'