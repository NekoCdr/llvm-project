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
        self.br_line_cast_func = line_number(
            "main.cpp", "// Break here in cast_func()."
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
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp", self.br_line_cast_func
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        use_dynamic = lldb.eDynamicCanRunTarget
        no_dynamic = lldb.eNoDynamicValues

        # Okay now run to cast breakpoint:
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        print("================== Get static var ==================")
        var_static = frame.FindVariable("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "A_2 *")
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())

        # We need to make sure that lldb_private::ValueObjectRecognizedValue
        # takes precedence over lldb_private::ValueObjectDynamicValue. Dynamic
        # should define the "input_var" type as "C_1 *", and Recognizer is
        # guided by user logic that defines the "input_var" type as "B_2 *". Now
        # make sure that the lldb_private::ValueObjectDynamicValue works fine.
        print("================== Get dynamic var ==================")
        var_dynamic = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_dynamic)
        self.assertTrue(var_dynamic.type.name == "C_1 *")
        self.assertTrue(var_dynamic.IsValid())
        self.assertTrue(var_dynamic.IsDynamic())

        # Now set up the type recognizer
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.generalHandler A_2")
        self.runCmd("type recognizer add -F RecognizerFormatter.generalHandler C_1")
        self.runCmd("type recognizer add -F RecognizerFormatter.handleVirtualDerivatives C_2")
        self.runCmd("type recognizer add -F RecognizerFormatter.handleVirtualDerivatives C_3")
        self.runCmd("type recognizer add -F RecognizerFormatter.handleVirtualDerivatives C_4")
        self.runCmd("type recognizer add -F RecognizerFormatter.handleA1Base A_1")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # downcast works fine.
        print("================== Get recognized downcast input_var ==================")
        var_recognized = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.type.name == "B_2 *")
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())

        # Okay, now continue to the next breakpoint for upcast
        threads = lldbutil.continue_to_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        var_static = frame.FindVariable("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "C_1 *")
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # upcast works fine.
        print("================== Get recognized upcast input_var ==================")
        var_recognized = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.type.name == "A_2 *")
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())

        # Okay, now continue to the next breakpoint for virtual downcast
        threads = lldbutil.continue_to_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        var_static = frame.FindVariable("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "A_2 *")
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # downcast works fine.
        print("================== Get recognized virtual downcast input_var ==================")
        var_recognized = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.type.name == "B_3 *")
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())

        # Okay, now continue to the next breakpoint for virtual upcast
        threads = lldbutil.continue_to_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        var_static = frame.FindVariable("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "C_2 *")
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # upcast works fine.
        print("================== Get recognized virtual upcast input_var ==================")
        var_recognized = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.type.name == "A_2 *")
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())

        # Okay, now continue to the next breakpoint for ambiguous downcast
        threads = lldbutil.continue_to_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        var_static = frame.FindVariable("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "A_1 *")
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # returns a static "A_1 *" instead of a dynamic "C_1 *"
        print("================== Try to get ambiguous recognized upcast input_var ==================")
        var_recognized = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.type.name == "A_1 *")
        self.assertTrue(var_recognized.IsValid())
        self.assertFalse(var_recognized.IsDynamic())
        # TODO: assert lldb error message
        # Currently ValueObjectRecognizedValue used AsyncErrorStream for errors,
        # but we can't get it's output via runCmd() or expect()

        # Okay, now continue to the next breakpoint for ambiguous upcast
        threads = lldbutil.continue_to_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        var_static = frame.FindVariable("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "C_1 *")
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # returns a static "C_1 *" instead of a dynamic "A_1 *"
        print("================== Try to get ambiguous recognized upcast input_var ==================")
        var_recognized = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.type.name == "C_1 *")
        self.assertTrue(var_recognized.IsValid())
        self.assertFalse(var_recognized.IsDynamic())
        # TODO: assert lldb error message
        # Currently ValueObjectRecognizedValue used AsyncErrorStream for errors,
        # but we can't get it's output via runCmd() or expect()

        # Okay, now continue to the next breakpoint for ambiguous upcast with
        # intermediate virtual bases
        threads = lldbutil.continue_to_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        var_static = frame.FindVariable("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "C_3 *")
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # returns a static "C_3 *" instead of a dynamic "A_1 *"
        print("================== Try to get ambiguous recognized upcast input_var ==================")
        var_recognized = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.type.name == "C_3 *")
        self.assertTrue(var_recognized.IsValid())
        self.assertFalse(var_recognized.IsDynamic())
        # TODO: assert lldb error message
        # Currently ValueObjectRecognizedValue used AsyncErrorStream for errors,
        # but we can't get it's output via runCmd() or expect()

        # Okay, now continue to the next breakpoint for ambiguous upcast with
        # intermediate direct and virtual bases
        threads = lldbutil.continue_to_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        var_static = frame.FindVariable("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "C_4 *")
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # returns a static "C_4 *" instead of a dynamic "A_1 *"
        print("================== Try to get ambiguous recognized upcast input_var ==================")
        var_recognized = frame.FindVariable("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.type.name == "C_4 *")
        self.assertTrue(var_recognized.IsValid())
        self.assertFalse(var_recognized.IsDynamic())
        # TODO: assert lldb error message
        # Currently ValueObjectRecognizedValue used AsyncErrorStream for errors,
        # but we can't get it's output via runCmd() or expect()

    # TODO: We need to refine the TypeRecognizer infrastructure so that it affects the expression evaluator result and remove this expectedFailureAll decorator
    @expectedFailureAll
    def test_expression_evaluator(self):
        """Test recognizing variables using the EvaluateExpression."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up our breakpoints:
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp", self.br_line_cast_func
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        use_dynamic = lldb.eDynamicCanRunTarget
        no_dynamic = lldb.eNoDynamicValues

        # Okay now run to cast breakpoint:
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)

        # Get static "input_var"
        var_static = frame.EvaluateExpression("input_var", no_dynamic)
        self.assertTrue(var_static)
        self.assertTrue(var_static.type.name == "A_2 *")

        # We need to make sure that lldb_private::ValueObjectRecognizedValue
        # takes precedence over lldb_private::ValueObjectDynamicValue. Dynamic
        # should define the "input_var" type as "C_1 *", and Recognizer is
        # guided by user logic that defines the "input_var" type as "B_2 *". Now
        #  make sure that the lldb_private::ValueObjectDynamicValue works fine.
        var_dynamic = frame.EvaluateExpression("input_var", use_dynamic)
        self.assertTrue(var_dynamic)
        self.assertTrue(var_dynamic.type.name == "C_1 *")

        # Now set up the type recognizer
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.recognizeType A_2")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # downcast works fine.
        var_recognized = frame.EvaluateExpression("input_var", use_dynamic)
        self.assertTrue(var_recognized)
        # TODO: delete this comment after removing expectedFailureAll decorator
        # The assertion below fails because the type recognizer doesn't affect
        # the expression evaluator result.
        self.assertTrue(var_recognized.type.name == "B_2 *")

    # This is the function to remove the recognizer in order to have a clean
    # state for the next test case.
    def cleanup(self):
        self.runCmd("type recognizer clear", check=False)