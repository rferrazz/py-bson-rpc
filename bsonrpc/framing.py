'''
'''
from .exceptions import FramingError


class JsonFramingRfc7464(object):

    @classmethod
    def extract_message(cls, raw_bytes):
        if len(raw_bytes) < 2:
            return None, raw_bytes
        if raw_bytes[0] != 0x1e:
            raise FramingError('Framing broken.')
        if b'\x0a' in raw_bytes:
            b_msg, rest = raw_bytes.split(b'\x0a', 1)
            return b_msg[1:], rest
        else:
            return None, raw_bytes

    @classmethod
    def into_frame(cls, message_bytes):
        return b'\x1e' + message_bytes + b'\x0a'


class JsonFramingNetstring(object):

    @classmethod
    def extract_message(cls, raw_bytes):
        if b':' not in raw_bytes:
            if len(raw_bytes) > 10:
                raise FramingError('Length information missing.')
            return None, raw_bytes
        msg_len, rest = raw_bytes.split(b':', 1)
        msg_len = int(msg_len)
        if len(rest) < msg_len + 1:
            return None, raw_bytes
        else:
            return rest[:msg_len], rest[(msg_len + 1):]

    @classmethod
    def into_frame(cls, message_bytes):
        msg_len = len(message_bytes)
        return bytes(str(msg_len), 'utf-8') + b':' + message_bytes + b','


class JsonFrameless(object):

    @classmethod
    def extract_message(cls, raw_bytes):
        if len(raw_bytes) < 2:
            return None, raw_bytes
        if not raw_bytes.startswith(b'{'):
            raise FramingError('JSON Object required.')
        stack = [123]  # {
        uniesc = 0
        poppers = {91: [93], 123: [125], 34: [34]}
        adders = {91: [34, 91, 123], 123: [34, 91, 123], 34: [92], 92: [117]}
        for idx in range(1, len(raw_bytes)):
            if not stack:
                return raw_bytes[:idx], raw_bytes[idx:]
            cbyte = raw_bytes[idx]
            if cbyte in poppers.get(stack[-1], []):
                stack.pop()
            elif cbyte in adders.get(stack[-1], []):
                stack.append(cbyte)
            elif stack[-1] == 92:
                stack.pop()
            elif stack[-1] == 117:
                uniesc += 1
                if uniesc >= 4:
                    stack = stack[:-2]
                    uniesc = 0
        return None, raw_bytes

    @classmethod
    def into_frame(cls, message_bytes):
        return message_bytes