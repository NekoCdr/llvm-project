from lldb import SBType, SBValue

def generalHandler(value: SBValue, internal_dict) -> SBType:
    supported_targets = [
        "A_1",
        "A_2",

        "B_2",
        "B_3",
    ]

    # Get target type from value data members
    assert value.GetChildMemberWithName("target").IsValid()
    target_type: SBValue = value.GetChildMemberWithName("target").value

    if target_type in supported_targets:
        derived_type: SBType = value.target.FindFirstType(target_type)
    else:
        raise NotImplementedError(f"Non-supported target type: {target_type}")

    assert derived_type.IsValid()
    if value.type.IsPointerType():
        derived_type = derived_type.GetPointerType()

    return derived_type

def handleVirtualDerivatives(value: SBValue, internal_dict) -> SBType:
    supported_targets = [
        "A_1",
        "A_2",
    ]

    # Get intermediate base from value children
    assert value.GetChildAtIndex(1).IsValid()
    intermediate: SBValue = value.GetChildAtIndex(1)

    # Get A_2 base from intermediate children
    assert intermediate.GetChildAtIndex(0).IsValid()
    a_2: SBValue = intermediate.GetChildAtIndex(0)

    # Get target type from A_2 data members
    assert a_2.GetChildMemberWithName("target").IsValid()
    target_type: SBValue = a_2.GetChildMemberWithName("target").value

    if target_type in supported_targets:
        derived_type: SBType = value.target.FindFirstType(target_type)
    else:
        raise NotImplementedError(f"Non-supported target type: {target_type}")

    assert derived_type.IsValid()
    if value.type.IsPointerType():
        derived_type = derived_type.GetPointerType()

    return derived_type

def handleA1Base(value: SBValue, internal_dict) -> SBType:
    supported_targets = [
        "C_1",
    ]

    # Get target type from value data members
    assert value.GetChildMemberWithName("a_1_target").IsValid()
    target_type: SBValue = value.GetChildMemberWithName("a_1_target").value

    if target_type in supported_targets:
        derived_type: SBType = value.target.FindFirstType(target_type)
    else:
        raise NotImplementedError(f"Non-supported target type: {target_type}")

    assert derived_type.IsValid()
    if value.type.IsPointerType():
        derived_type = derived_type.GetPointerType()

    return derived_type
