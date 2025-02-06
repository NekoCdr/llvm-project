"""
Use lldb Python API to test ValueObject type recognizer
"""


import lldb
from lldbsuite.test.decorators import *
from lldbsuite.test.lldbtest import *
from lldbsuite.test import lldbutil


class RecognizedValueTestCase(TestBase):
    def setUp(self):
        # Call super's setUp().
        TestBase.setUp(self)

        # Execute the cleanup function during test case tear down.
        self.addTearDownHook(self.cleanup)

        # Find the line number to break for main.cpp.
        self.br_line_downcast = line_number(
            "main.cpp", "// Break here in downcast()."
        )
        self.br_line_downcast_w_multiply = line_number(
            "main.cpp", "// Break here in downcast_w_multiply()."
        )

        # Prepare executable.
        self.build()
        self.exe = self.getBuildArtifact("a.out")

    def test_find_variable(self):
        """Test recognizing variables using the FindVariable."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up our breakpoints:
        br_downcast = target.BreakpointCreateByLocation(
            "main.cpp", self.br_line_downcast
        )
        br_downcast_w_multiply = target.BreakpointCreateByLocation(
            "main.cpp", self.br_line_downcast_w_multiply
        )
        self.assertTrue(br_downcast, VALID_BREAKPOINT)
        self.assertTrue(br_downcast_w_multiply, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        use_dynamic = lldb.eDynamicCanRunTarget
        no_dynamic = lldb.eNoDynamicValues

        # Okay now run to downcast breakpoint:
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_downcast)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "a"
        a_static = frame.FindVariable("a", no_dynamic)
        self.assertTrue(a_static)
        self.assertTrue(a_static.type.name == "A *")

        # We need to make sure that lldb_private::ValueObjectRecognizedValue
        # takes precedence over lldb_private::ValueObjectDynamicValue.
        # Dynamic should define the "a" type as "C *", and Recognizer is guided
        # by user logic that defines the "a" type as "B *". Now make sure that
        # the lldb_private::ValueObjectDynamicValue works fine.
        a_dynamic = frame.FindVariable("a", use_dynamic)
        self.assertTrue(a_dynamic)
        self.assertTrue(a_dynamic.type.name == "C *")

        # Now set up the type recognizer
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.recognizeType A")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue works
        # fine.
        a_recognized = frame.FindVariable("a", use_dynamic)
        self.assertTrue(a_recognized)
        self.assertTrue(a_recognized.type.name == "B *")

        # Okay, now continue to the downcast with multiply bases
        threads = lldbutil.continue_to_breakpoint(process, br_downcast_w_multiply)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "a"
        a_static = frame.FindVariable("a", no_dynamic)
        self.assertTrue(a_static)
        self.assertTrue(a_static.type.name == "A *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue works
        # fine.
        a_recognized = frame.FindVariable("a", use_dynamic)
        self.assertTrue(a_recognized)
        self.assertTrue(a_recognized.type.name == "B2 *")

    # TODO: We need to refine the TypeRecognizer infrastructure so that it affects the expression evaluator result and remove this expectedFailureAll decorator
    @expectedFailureAll
    def test_expression_evaluator(self):
        """Test recognizing variables using the EvaluateExpression."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up our breakpoints:
        br_downcast = target.BreakpointCreateByLocation(
            "main.cpp", self.br_line_downcast
        )
        self.assertTrue(br_downcast, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        use_dynamic = lldb.eDynamicCanRunTarget
        no_dynamic = lldb.eNoDynamicValues

        # Okay now run to f_breakpoint:
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_downcast)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "a"
        a_static = frame.EvaluateExpression("a", no_dynamic)
        self.assertTrue(a_static)
        self.assertTrue(a_static.type.name == "A *")

        # We need to make sure that lldb_private::ValueObjectRecognizedValue
        # takes precedence over lldb_private::ValueObjectDynamicValue.
        # Dynamic should define the "a" type as "C *", and Recognizer is guided
        # by user logic that defines the "a" type as "B *". Now make sure that
        # the lldb_private::ValueObjectDynamicValue works fine.
        a_dynamic = frame.EvaluateExpression("a", use_dynamic)
        self.assertTrue(a_dynamic)
        self.assertTrue(a_dynamic.type.name == "C *")

        # Now set up the type recognizer
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.recognizeType A")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue works
        # fine.
        a_recognized = frame.EvaluateExpression("a", use_dynamic)
        self.assertTrue(a_recognized)
        # TODO: delete this comment after removing expectedFailureAll decorator
        # The assertion below fails because the type recognizer doesn't affect
        # the expression evaluator result.
        self.assertTrue(a_recognized.type.name == "B *")

    # This is the function to remove the recognizer in order to have a clean
    # state for the next test case.
    def cleanup(self):
        self.runCmd("type recognizer clear", check=False)