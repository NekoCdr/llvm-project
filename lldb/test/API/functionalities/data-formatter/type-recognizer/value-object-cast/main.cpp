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
};

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

//===-- [Function section] ------------------------------------------------===//

template <class T> void cast_func(T *input_var) {
  [[maybe_unused]] int o{0}; // Break here in cast_func().
}

int main() {
  // Prepare objects
  B_2 b2_obj;
  C_1 c1_obj;
  C_2 c2_obj;
  C_3 c3_obj;
  C_4 c4_obj;

  // Downcast from A_2 to B_2
  c1_obj.target = CastTarget::B_2;
  cast_func<A_2>(&c1_obj);

  // Upcast from C_1 to A_2
  c1_obj.target = CastTarget::A_2;
  cast_func<C_1>(&c1_obj);

  // Downcast from virtual A_2 to B_3
  c2_obj.target = CastTarget::B_3;
  cast_func<A_2>(&c2_obj);

  // Upcast from C_2 to virtual A_2
  c2_obj.target = CastTarget::A_2;
  cast_func<C_2>(&c2_obj);

  // Ambiguous downcast from A_1 to C_1
  b2_obj.a_1_target = CastTarget::C_1;
  cast_func<A_1>(&b2_obj);

  // Ambiguous upcast from C_1 to A_1
  c1_obj.target = CastTarget::A_1;
  cast_func<C_1>(&c1_obj);

  // Ambiguous upcast from C_3 to A_1
  c3_obj.target = CastTarget::A_1;
  cast_func<C_3>(&c3_obj);

  // Ambiguous upcast from C_4 to A_1
  c4_obj.target = CastTarget::A_1;
  cast_func<C_4>(&c4_obj);
}
