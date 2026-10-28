coder = typecoders.registry.get_coder(Order)
print(coder)                        # RowCoder
print(coder.is_deterministic())     # True
