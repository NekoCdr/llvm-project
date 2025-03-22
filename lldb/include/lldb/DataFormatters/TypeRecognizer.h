//===-- TypeRecognizer.h ----------------------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#ifndef LLDB_DATAFORMATTERS_TYPERECOGNIZER_H
#define LLDB_DATAFORMATTERS_TYPERECOGNIZER_H

#include <cstdint>
#include <memory>
#include <string>

#include "lldb/Core/Address.h"
#include "lldb/Core/Debugger.h"
#include "lldb/Interpreter/CommandInterpreter.h"
#include "lldb/Symbol/CompilerType.h"
#include "lldb/Utility/Status.h"
#include "lldb/ValueObject/ValueObject.h"
#include "lldb/lldb-enumerations.h"

namespace lldb_private {

class TypeRecognizerImpl {
public:
  class Flags {
  public:
    Flags() = default;

    Flags(const Flags &other) = default;

    Flags(uint32_t value) : m_flags(value) {}

    Flags &operator=(const Flags &rhs) {
      if (&rhs != this)
        m_flags = rhs.m_flags;

      return *this;
    }

    Flags &operator=(const uint32_t &rhs) {
      m_flags = rhs;
      return *this;
    }

    Flags &Clear() {
      m_flags = 0;
      return *this;
    }

    bool GetCascades() const {
      return (m_flags & lldb::eTypeOptionCascade) == lldb::eTypeOptionCascade;
    }

    Flags &SetCascades(bool value = true) {
      if (value)
        m_flags |= lldb::eTypeOptionCascade;
      else
        m_flags &= ~lldb::eTypeOptionCascade;
      return *this;
    }

    bool GetSkipPointers() const {
      return (m_flags & lldb::eTypeOptionSkipPointers) ==
             lldb::eTypeOptionSkipPointers;
    }

    Flags &SetSkipPointers(bool value = true) {
      if (value)
        m_flags |= lldb::eTypeOptionSkipPointers;
      else
        m_flags &= ~lldb::eTypeOptionSkipPointers;
      return *this;
    }

    bool GetSkipReferences() const {
      return (m_flags & lldb::eTypeOptionSkipReferences) ==
             lldb::eTypeOptionSkipReferences;
    }

    Flags &SetSkipReferences(bool value = true) {
      if (value)
        m_flags |= lldb::eTypeOptionSkipReferences;
      else
        m_flags &= ~lldb::eTypeOptionSkipReferences;
      return *this;
    }

    bool GetNonCacheable() const {
      return (m_flags & lldb::eTypeOptionNonCacheable) ==
             lldb::eTypeOptionNonCacheable;
    }

    Flags &SetNonCacheable(bool value = true) {
      if (value)
        m_flags |= lldb::eTypeOptionNonCacheable;
      else
        m_flags &= ~lldb::eTypeOptionNonCacheable;
      return *this;
    }

  private:
    uint32_t m_flags = lldb::eTypeOptionCascade;
  };

  TypeRecognizerImpl(const Flags &flags, const char *function_name,
                     const char *python_script = nullptr)
      : m_flags(flags), m_function_name(), m_python_script() {
    if (function_name)
      m_function_name.assign(function_name);
    if (python_script)
      m_python_script.assign(python_script);
  }

  uint32_t &GetRevision() { return m_my_revision; }

  bool Cascades() const { return m_flags.GetCascades(); }

  bool SkipsPointers() const { return m_flags.GetSkipPointers(); }

  bool SkipsReferences() const { return m_flags.GetSkipReferences(); }

  bool NonCacheable() const { return m_flags.GetNonCacheable(); }

  std::string GetDescription() {
    StreamString sstr;
    sstr.Printf(
        "%s%s%s Python function %s", Cascades() ? "" : " (not cascading)",
        SkipsPointers() ? " (skip pointers)" : "",
        SkipsReferences() ? " (skip references)" : "", m_function_name.c_str());

    return std::string(sstr.GetString());
  }

  typedef std::shared_ptr<TypeRecognizerImpl> SharedPointer;

  Status RecognizeObjectType(ValueObject *valobj, CompilerType &output_ct,
                             Address &output_addr) {
    if (!valobj)
      return Status("No valobj");

    lldb::TargetSP target_sp(valobj->GetTargetSP());

    if (!target_sp)
      return Status("No target");

    ScriptInterpreter *script_interpreter =
        target_sp->GetDebugger().GetScriptInterpreter();

    if (!script_interpreter)
      return Status("No ScriptInterpreter");

    return script_interpreter->RecognizeType(
        m_function_name.c_str(), valobj->GetSP(), output_ct, output_addr);
  }

private:
  uint32_t m_my_revision = 0;
  Flags m_flags;
  std::string m_function_name;
  std::string m_python_script;
};

} // namespace lldb_private

#endif // LLDB_DATAFORMATTERS_TYPERECOGNIZER_H
