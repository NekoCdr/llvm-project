/// Non-Virtual Inheritance:
/// --------------------------
///
///  [A_1]  [A_1] [A_2]
///    |       \   /
///  [B_1]     [B_2]
///      \     /
///       [C_1]
///
///
///  [X_1<T, K>]
///       |
///  [Y_1<T, K>]
///
///
///  [NS::X_2]
///      |
///  [NS::Y_2]
///
///
/// Virtual Inheritance:
/// --------------------------
///
///       [A_2]
///      /     \
///  [B_3]     [B_4]
///      \     /
///       [C_2]
///
///
///  [A_1]    [A_1] [A_2]
///    |         \   /
///  [B_1]       [B_2]
///    |           |
///   virt       virt
///     \         /
///    [--- C_3 ---]
///
///
///  [A_1]    [A_1] [A_2]
///    |         \   /
///  [B_1]       [B_2]
///    |           |
///    |         virt
///     \         /
///    [--- C_4 ---]
///

enum class CastTarget {
  A_1,
  A_2,

  B_1,
  B_2,
  B_3,
  B_4,

  C_1,
  C_2,
  C_3,
  C_4,

  X_1, // namespace NS
  X_2, // namespace NS

  Y_1,
  Y_2,
};

//===-- [Base classes] ----------------------------------------------------===//

struct A_1 {
  virtual void foo() {}
  CastTarget a_1_target{CastTarget::A_1};
  CastTarget a_1_member{CastTarget::A_1};
};

struct A_2 {
  virtual void bar() {}
  CastTarget target{CastTarget::A_2};
  CastTarget a_2_member{CastTarget::A_2};
};

template <typename T, typename K> struct X_1 {
  virtual void bar() {}
  CastTarget target{CastTarget::X_1};
  CastTarget x_1_member{CastTarget::X_1};
};

namespace NS {

struct X_2 {
  virtual void bar() {}
  CastTarget target{CastTarget::X_2};
  CastTarget x_2_member{CastTarget::X_2};
};

} // namespace NS

//===-- [Intermediate classes] --------------------------------------------===//

struct B_1 : A_1 {
  CastTarget b_1_member{CastTarget::B_1};
};

struct B_2 : A_2, A_1 {
  CastTarget b_2_member{CastTarget::B_2};
};

struct B_3 : virtual A_2 {
  CastTarget b_3_member{CastTarget::B_3};
};

struct B_4 : virtual A_2 {
  CastTarget b_4_member{CastTarget::B_4};
};

//===-- [Derived classes] -------------------------------------------------===//

struct C_1 : B_1, B_2 {
  CastTarget c_1_member{CastTarget::C_1};
};

struct C_2 : B_3, B_4 {
  CastTarget c_2_member{CastTarget::C_2};
};

struct C_3 : virtual B_1, virtual B_2 {
  CastTarget c_3_member{CastTarget::C_3};
};

struct C_4 : B_1, virtual B_2 {
  CastTarget c_4_member{CastTarget::C_4};
};

template <typename T, typename K> struct Y_1 : X_1<T, K> {
  CastTarget target{CastTarget::Y_1};
  CastTarget y_1_member{CastTarget::Y_1};
};

namespace NS {

struct Y_2 : X_2 {
  CastTarget target{CastTarget::Y_2};
  CastTarget y_2_member{CastTarget::Y_2};
};

} // namespace NS

//===-- [Test cases] ------------------------------------------------------===//

using breakpoint = int;

int main() {
  {
    C_1 obj;
    obj.target = CastTarget::B_2;
    [[maybe_unused]] A_2 *ptr{&obj};
    [[maybe_unused]] breakpoint downcast_A2_to_B2;
  }
  {
    C_1 obj;
    obj.target = CastTarget::A_2;
    [[maybe_unused]] C_1 *ptr{&obj};
    [[maybe_unused]] breakpoint upcast_C1_to_A2;
  }
  {
    C_2 obj;
    obj.target = CastTarget::B_3;
    [[maybe_unused]] A_2 *ptr{&obj};
    [[maybe_unused]] breakpoint downcast_virt_A2_to_B3;
  }
  {
    C_2 obj;
    obj.target = CastTarget::A_2;
    [[maybe_unused]] C_2 *ptr{&obj};
    [[maybe_unused]] breakpoint upcast_C2_to_virt_A2;
  }
  {
    B_2 obj;
    obj.a_1_target = CastTarget::C_1;
    [[maybe_unused]] A_1 *ptr{&obj};
    [[maybe_unused]] breakpoint ambiguous_downcast_A1_to_C1;
  }
  {
    C_1 obj;
    obj.target = CastTarget::A_1;
    [[maybe_unused]] C_1 *ptr{&obj};
    [[maybe_unused]] breakpoint ambiguous_upcast_C1_to_A1;
  }
  {
    C_3 obj;
    obj.target = CastTarget::A_1;
    [[maybe_unused]] C_3 *ptr{&obj};
    [[maybe_unused]] breakpoint ambiguous_upcast_C3_to_A1;
  }
  {
    C_4 obj;
    obj.target = CastTarget::A_1;
    [[maybe_unused]] C_4 *ptr{&obj};
    [[maybe_unused]] breakpoint ambiguous_upcast_C4_to_A1;
  }
  {
    Y_1<int, char> obj;
    obj.target = CastTarget::X_1;
    [[maybe_unused]] Y_1<int, char> *ptr{&obj};
    [[maybe_unused]] breakpoint template_upcast_Y1_to_X1;
  }
  {
    NS::Y_2 obj;
    obj.target = CastTarget::X_2;
    [[maybe_unused]] NS::Y_2 *ptr{&obj};
    [[maybe_unused]] breakpoint qualified_upcast_Y2_to_X2;
  }
}
