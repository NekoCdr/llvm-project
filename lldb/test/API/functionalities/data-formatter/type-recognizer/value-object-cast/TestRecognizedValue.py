import lldb
from lldbsuite.test.lldbtest import TestBase, line_number, VALID_TARGET, VALID_BREAKPOINT, PROCESS_STOPPED
from lldbsuite.test import lldbutil

USE_DYNAMIC = lldb.eDynamicCanRunTarget
NO_DYNAMIC = lldb.eNoDynamicValues

class RecognizedValueTestCase(TestBase):
    def setUp(self):
        TestBase.setUp(self)

        # Execute the cleanup function during test case tear down.
        self.addTearDownHook(self.cleanup)

        # Prepare executable.
        self.build()
        self.exe = self.getBuildArtifact("a.out")

    def test_downcast_A2_to_B2(self):
        """Test simple downcasting and recognizer precedencing."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "downcast_A2_to_B2")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "A_2 *")

        # Now make sure that the lldb_private::ValueObjectDynamicValue define
        # the type as "C_1 *", because Recognizer not registered yet.
        var_dynamic = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_dynamic)
        self.assertTrue(var_dynamic.IsValid())
        self.assertTrue(var_dynamic.IsDynamic())
        self.assertTrue(var_dynamic.type.name == "C_1 *")

        # Now set up the type recognizer.
        # lldb_private::ValueObjectRecognizedValue takes precedence over
        # lldb_private::ValueObjectDynamicValue.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.generalHandler A_2")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # downcast works fine and define the type as "B_2 *".
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "B_2 *")

    def test_upcast_C1_to_A2(self):
        """Test simple upcasting."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "upcast_C1_to_A2")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.generalHandler C_1")

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "C_1 *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # upcast works fine.
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "A_2 *")

    def test_downcast_virt_A2_to_B3(self):
        """Test downcasting from the virtual base."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "downcast_virt_A2_to_B3")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.generalHandler A_2")

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "A_2 *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # downcast works fine.
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "B_3 *")

    def test_upcast_C2_to_virt_A2(self):
        """Test upcasting to the virtual base."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "upcast_C2_to_virt_A2")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.handleDerivedToVirtualBase C_2")

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "C_2 *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # upcast works fine.
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "A_2 *")

    def test_ambiguous_downcast_A1_to_C1(self):
        """Test downcasting from the ambiguous base with non-virtual inheritance."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "ambiguous_downcast_A1_to_C1")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.handleA1Base A_1")

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "A_1 *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # returns a static "A_1 *" instead of a dynamic "C_1 *".
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertFalse(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "A_1 *")
        # FIXME: assert lldb error message
        # Currently ValueObjectRecognizedValue used AsyncErrorStream for errors,
        # but we can't get it's output via runCmd() or expect().

    def test_ambiguous_upcast_C1_to_A1(self):
        """Test upcasting to the ambiguous base with non-virtual inheritance."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "ambiguous_upcast_C1_to_A1")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.generalHandler C_1")

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "C_1 *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # returns a static "C_1 *" instead of a dynamic "A_1 *".
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertFalse(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "C_1 *")
        # FIXME: assert lldb error message
        # Currently ValueObjectRecognizedValue used AsyncErrorStream for errors,
        # but we can't get it's output via runCmd() or expect().

    def test_ambiguous_upcast_C3_to_A1(self):
        """Test upcasting to the ambiguous base with virtual inheritance."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "ambiguous_upcast_C3_to_A1")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.handleDerivedToVirtualBase C_3")

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "C_3 *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # returns a static "C_3 *" instead of a dynamic "A_1 *".
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertFalse(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "C_3 *")
        # FIXME: assert lldb error message
        # Currently ValueObjectRecognizedValue used AsyncErrorStream for errors,
        # but we can't get it's output via runCmd() or expect().

    def test_ambiguous_upcast_C4_to_A1(self):
        """Test upcasting to the ambiguous base with virtual and non-virtual inheritance."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "ambiguous_upcast_C4_to_A1")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.handleDerivedToVirtualBase C_4")

        # Get static "ptr"
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "C_4 *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # returns a static "C_4 *" instead of a dynamic "A_1 *".
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertFalse(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "C_4 *")
        # FIXME: assert lldb error message
        # Currently ValueObjectRecognizedValue used AsyncErrorStream for errors,
        # but we can't get it's output via runCmd() or expect().

    def test_template_upcast_Y1_to_X1(self):
        """Test template upcasting."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "template_upcast_Y1_to_X1")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.generalHandler 'Y_1<int, char>'")

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "Y_1<int, char> *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # upcast works fine.
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "X_1<int, char> *")

    def test_qualified_upcast_Y2_to_X2(self):
        """Test qualified upcasting."""
        # Create a target from the debugger.
        target = self.dbg.CreateTarget(self.exe)
        self.assertTrue(target, VALID_TARGET)

        # Set up breakpoint.
        br_cast_func = target.BreakpointCreateByLocation(
            "main.cpp",
            line_number("main.cpp", "qualified_upcast_Y2_to_X2")
        )
        self.assertTrue(br_cast_func, VALID_BREAKPOINT)

        # Now launch the process, and do not stop at the entry point.
        process = target.LaunchSimple(None, None, self.get_process_working_directory())
        self.assertState(process.GetState(), lldb.eStateStopped, PROCESS_STOPPED)

        # Now run to cast breakpoint.
        threads = lldbutil.get_threads_stopped_at_breakpoint(process, br_cast_func)
        self.assertEqual(len(threads), 1)
        thread = threads[0]

        frame = thread.GetFrameAtIndex(0)
        assert frame.IsValid()

        # Now set up the type recognizer.
        self.runCmd("script import RecognizerFormatter")
        self.runCmd("type recognizer add -F RecognizerFormatter.generalHandler NS::Y_2")

        # Get static "ptr".
        var_static = frame.FindVariable("ptr", NO_DYNAMIC)
        self.assertTrue(var_static)
        self.assertTrue(var_static.IsValid())
        self.assertFalse(var_static.IsDynamic())
        self.assertTrue(var_static.type.name == "NS::Y_2 *")

        # Then make sure that the lldb_private::ValueObjectRecognizedValue
        # upcast works fine.
        var_recognized = frame.FindVariable("ptr", USE_DYNAMIC)
        self.assertTrue(var_recognized)
        self.assertTrue(var_recognized.IsValid())
        self.assertTrue(var_recognized.IsDynamic())
        self.assertTrue(var_recognized.type.name == "NS::X_2 *")

    # This is the function to remove the recognizer in order to have a clean
    # state for the next test case.
    def cleanup(self):
        self.runCmd("type recognizer clear", check=False)
