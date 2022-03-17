def test_base():
    from nip import convert, dump
    obj = {
        'first': 1,
        'second': '2'
    }
    print(dump('features/pin/dumps/obj.nip', obj))

