from lldb import SBType, SBValue

def generalHandler(value: SBValue, internal_dict) -> SBType:
    # Consult inheritance graphs for C_1, C_2 (virt_A2_to_B3), Y_1 and Y_2<T, K>
    # in main.cpp for additional context
    supported_targets = (
        "A_1",
        "A_2",

        "B_2",
        "B_3",

        "NS::X_2",
        "X_1<int, char>",
    )

    TARGETS_MAP = {
        "X_2": "NS::X_2",
        "X_1": "X_1<int, char>",
    }

    # Get target type from value data members
    assert value.GetChildMemberWithName("target").IsValid()
    target_type: SBValue = value.GetChildMemberWithName("target").value

    if target_type in TARGETS_MAP:
        target_type = TARGETS_MAP[target_type]

    if target_type in supported_targets:
        derived_type: SBType = value.target.FindFirstType(target_type)
    else:
        raise NotImplementedError(f"Non-supported target type: {target_type}")

    assert derived_type.IsValid()
    if value.type.IsPointerType():
        derived_type = derived_type.GetPointerType()

    return derived_type

def handleDerivedToVirtualBase(value: SBValue, internal_dict) -> SBType:
    # Consult inheritance graphs for C_2, C_3, and C_4 in main.cpp for
    # additional context
    supported_targets = (
        "A_1",
        "A_2",
    )

    # Get intermediate base from value children
    assert value.GetChildAtIndex(1).IsValid()
    intermediate: SBValue = value.GetChildAtIndex(1)
    # TODO: Fix. Ассерт на B_2 игнорируется.
    assert intermediate.type.name in ("B_2", "B_4")

    # Get A_2 base from intermediate children
    # FIXME: GetChildMemberWithName should fully support class member lookup.
    # For now we explicitly use intermediate base to get to the data member.
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
    # Consult inheritance graph for C_1 in main.cpp for additional context
    supported_targets = (
        "C_1",
    )

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
