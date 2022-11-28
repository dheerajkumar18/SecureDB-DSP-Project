import hashlib
import psycopg2.extensions
import hmac
from Crypto.Cipher import AES

# secret key
password = b'402xy5#'
key = b'.\x91\xfd\xa5\xdd%T\x05\xf5\x14\x87\xc0\xe3\xd8\x81\x82'
header = b'header'

encryption_columns = ['"user_auth_user"."username"', '"user_auth_user"."email"',
                      '"user_auth_user"."first_name"', '"user_auth_user"."last_name"']


def create_encryption_block(data):
    hmac_for_search = hmac.new(password, bytes(data, 'utf-8'), hashlib.sha3_256).digest()
    cipher = AES.new(key, AES.MODE_GCM)
    cipher.update(header)
    cipher_text, tag = cipher.encrypt_and_digest(bytes(data, 'utf-8'))
    nonce = cipher.nonce
    print("Nonce " + str(nonce) + "Tag " + str(tag) + "Cipher Text " + str(cipher_text))
    final_data = nonce + tag + hmac_for_search + cipher_text
    return final_data


def decrypt_encryption_block(encryption_block):
    encryption_block = bytes(encryption_block)
    nonce = encryption_block[:16]
    tag = encryption_block[16:32]
    decrypt_cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypt_cipher.update(header)
    plain_text = decrypt_cipher.decrypt_and_verify(encryption_block[64:], tag)
    print("Nonce " + str(nonce) + "Tag " + str(tag) + "Plain_text " + plain_text.decode('utf-8'))
    return plain_text.decode('utf-8')


class CustomCursor(psycopg2.extensions.cursor):
    def execute(self, query, vars=None):
        if vars:
            print(f"Parameters before modification: {vars}")
            vars = list(vars)
        print(f"Query before modification: {query}")
        if "WHERE" in query and "UPDATE" not in query:
            filters = query.split('WHERE')[1].split('%s')
            for index in range(len(filters)):
                match = [each for each in encryption_columns if each+" =" in filters[index]]
                if match:
                    vars[index] = hmac.new(password, bytes(vars[index].adapted, 'utf-8'), hashlib.sha3_256).digest()
                    query = query.replace(match[0] + " =", f"substring({match[0]}, 33, 32) =")
        if "INSERT" in query:
            insertion_attributes = query.split(",")
            for index in range(len(insertion_attributes)):
                if [True for each in encryption_columns if each.split('.')[1] in insertion_attributes[index]]:
                    vars[index] = create_encryption_block(vars[index].adapted)
        if vars:
            vars = tuple(vars)
        print(f"Query after modification: {query}")
        print(f"Parameters after modification: {vars}")
        super().execute(query, vars)

    def decrypt_results(self, results):
        filters = self.query.decode('utf-8').split(",")
        for result_index in range(len(results)):
            results[result_index] = list(results[result_index])
            for each in range(len(results[result_index])):
                if [True for each_filter in encryption_columns if each_filter in filters[each]]:
                    results[result_index][each] = decrypt_encryption_block(results[result_index][each])
            results[result_index] = tuple(results[result_index])

    def fetchall(self):
        results = super().fetchall()
        self.decrypt_results(results)
        return results

    def fetchmany(self, size=None):
        results = super().fetchmany(size)
        self.decrypt_results(results)
        return results

    def fetchone(self):
        result = super().fetchone()
        filters = self.query.decode('utf-8').split(",")
        if result:
            result = list(result)
            for each in range(len(result)):
                if [True for each_filter in encryption_columns if each_filter in filters[each]]:
                    result[each] = decrypt_encryption_block(result[each])
            result = tuple(result)
        return result
