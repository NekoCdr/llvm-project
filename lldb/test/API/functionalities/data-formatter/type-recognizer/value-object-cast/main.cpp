enum class ObjType {
  eTypeA = 0,
  eTypeB = 1,
  eTypeB2 = 2,
};

//===-- [Simple downcast section] -----------------------------------------===//
struct A {
  A(ObjType type) : OType(type) {}
  virtual void foo() {}
  int a_member{11};
  ObjType OType{ObjType::eTypeA};
};

struct B : A {
  int b_member{12};
  B() : A(ObjType::eTypeB) {}
};

struct C : B {
  int c_member{13};
};

void downcast(A *a) {
  int o{0}; // Break here in downcast().
}

//===-- [Multiply based downcast section] ---------------------------------===//
struct A2 {
  virtual void zoo() {}
  int a2_member{21};
};

struct B2 : A2, A {
  int b2_member{22};
  B2() : A(ObjType::eTypeB2) {}
};

struct C2 : B2 {
  int c2_member{23};
};

void downcast_w_multiply(A *a) {
  int o{0}; // Break here in downcast_w_multiply().
}

//===-- [Main section] ----------------------------------------------------===//
int main() {
  C b;
  downcast(&b);

  C2 b2;
  downcast_w_multiply(&b2);
}
