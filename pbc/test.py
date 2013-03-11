from ctypes import *
ibc = cdll.LoadLibrary('./libibc.so.1.0.1')
ibc.init_pairing(5, 1, 0)
ibc.read_share()
strin = 'ajoy91ad@gmail.com'
c_id = (c_char * 40)()
c_id.value = strin
ibc.hash_id_s(c_id)