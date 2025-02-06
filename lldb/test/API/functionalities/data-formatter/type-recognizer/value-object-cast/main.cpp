enum class ObjType {
  eTypeA = 0,
  eTypeB = 1,
};

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

int main() {
  C b;
  downcast(&b);
}
