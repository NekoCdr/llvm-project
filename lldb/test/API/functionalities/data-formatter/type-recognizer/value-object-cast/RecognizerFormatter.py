from lldb import SBType, SBValue

def recognizeType(value: SBValue, internal_dict) -> SBType:
    assert value.GetChildMemberWithName('OType').IsValid()
    o_type: SBValue = value.GetChildMemberWithName("OType").value
    if o_type == "eTypeA":
        derived_type: SBType = value.target.FindFirstType("A")
    elif o_type == "eTypeB":
        derived_type: SBType = value.target.FindFirstType("B")
    else:
        raise NotImplementedError(o_type)

    assert derived_type.IsValid()
    if value.type.IsPointerType():
        derived_type = derived_type.GetPointerType()

    return derived_type
