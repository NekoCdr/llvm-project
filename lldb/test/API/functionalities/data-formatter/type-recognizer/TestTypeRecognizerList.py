from lldbsuite.test.lldbtest import TestBase


class TypeRecognizerListTestCase(TestBase):
    def test_type_recognizer_list_type(self):
        # Test that the type argument works fine and list only specified type
        self.runCmd("type recognizer add -F testFunc Foo")
        self.runCmd("type recognizer add -F testFunc Boo")
        self.expect(
            "type recognizer list",
            substrs=[
                "Foo:  Python function testFunc",
                "Boo:  Python function testFunc"
            ]
        )
        self.expect(
            "type recognizer list Foo",
            substrs=["Foo:  Python function testFunc"]
        )
        self.expect(
            "type recognizer list Foo",
            substrs=["Boo:  Python function testFunc"],
            matching=False
        )

    def test_type_recognizer_list_category(self):
        # Test that the '-w' argument works fine and list only "default"
        # category items
        self.expect(
            "type recognizer list -w default",
            patterns=["^-+\nCategory: default\n-+\nno matching results found\.$"]
        )
