from apache_beam.coders import PickleCoder

coder = PickleCoder()
coder.encode({"b": 1, "a": 2})
# b'\x80\x05...}\x94(\x8c\x01b\x94K\x01\x8c\x01a\x94K\x02u.'
coder.encode({"a": 2, "b": 1})
# b'\x80\x05...}\x94(\x8c\x01a\x94K\x02\x8c\x01b\x94K\x01u.'
