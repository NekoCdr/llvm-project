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

//===-- [Function section] ------------------------------------------------===//

int main() {
  // Downcast from A_2 to B_2
  {
    C_1 c1_obj;
    c1_obj.target = CastTarget::B_2;
    [[maybe_unused]] A_2 *ptr{&c1_obj};
    [[maybe_unused]] int downcast_A2_to_B2{0};
  }

  // Upcast from C_1 to A_2
  {
    C_1 c1_obj;
    c1_obj.target = CastTarget::A_2;
    [[maybe_unused]] C_1 *ptr{&c1_obj};
    [[maybe_unused]] int upcast_C1_to_A2{0};
  }

  // Downcast from virtual A_2 to B_3
  {
    C_2 c2_obj;
    c2_obj.target = CastTarget::B_3;
    [[maybe_unused]] A_2 *ptr{&c2_obj};
    [[maybe_unused]] int downcast_virt_A2_to_B3{0};
  }

  // Upcast from C_2 to virtual A_2
  {
    C_2 c2_obj;
    c2_obj.target = CastTarget::A_2;
    [[maybe_unused]] C_2 *ptr{&c2_obj};
    [[maybe_unused]] int upcast_C2_to_virt_A2{0};
  }

  // Ambiguous downcast from A_1 to C_1
  {
    B_2 b2_obj;
    b2_obj.a_1_target = CastTarget::C_1;
    [[maybe_unused]] A_1 *ptr{&b2_obj};
    [[maybe_unused]] int ambiguous_downcast_A1_to_C1{0};
  }

  // Ambiguous upcast from C_1 to A_1
  {
    C_1 c1_obj;
    c1_obj.target = CastTarget::A_1;
    [[maybe_unused]] C_1 *ptr{&c1_obj};
    [[maybe_unused]] int ambiguous_upcast_C1_to_A1{0};
  }

  // Ambiguous upcast from C_3 to A_1
  {
    C_3 c3_obj;
    c3_obj.target = CastTarget::A_1;
    [[maybe_unused]] C_3 *ptr{&c3_obj};
    [[maybe_unused]] int ambiguous_upcast_C3_to_A1{0};
  }

  // Ambiguous upcast from C_4 to A_1
  {
    C_4 c4_obj;
    c4_obj.target = CastTarget::A_1;
    [[maybe_unused]] C_4 *ptr{&c4_obj};
    [[maybe_unused]] int ambiguous_upcast_C4_to_A1{0};
  }

  // template upcast from Y_1 to X_1
  {
    Y_1<int, char> y1_obj;
    y1_obj.target = CastTarget::X_1;
    [[maybe_unused]] Y_1<int, char> *ptr{&y1_obj};
    [[maybe_unused]] int template_upcast_Y1_to_X1{0};
  }

  // qualified upcast from Y_2 to X_2
  {
    NS::Y_2 y2_obj;
    y2_obj.target = CastTarget::X_2;
    [[maybe_unused]] NS::Y_2 *ptr{&y2_obj};
    [[maybe_unused]] int qualified_upcast_Y2_to_X2{0};
  }
}
