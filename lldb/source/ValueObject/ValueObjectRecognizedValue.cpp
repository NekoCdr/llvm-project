//===-- ValueObjectRecognizedValue.cpp ------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "lldb/ValueObject/ValueObjectRecognizedValue.h"

#include "lldb/Core/Address.h"
#include "lldb/Core/Value.h"
#include "lldb/DataFormatters/TypeRecognizer.h"
#include "lldb/Symbol/CompilerType.h"
#include "lldb/Symbol/Type.h"
#include "lldb/Target/ExecutionContext.h"
#include "lldb/Utility/DataExtractor.h"
#include "lldb/Utility/LLDBLog.h"
#include "lldb/Utility/Log.h"
#include "lldb/Utility/Scalar.h"
#include "lldb/Utility/Status.h"
#include "lldb/ValueObject/ValueObject.h"
#include "lldb/lldb-defines.h"
#include "lldb/lldb-forward.h"
#include "lldb/lldb-types.h"

#include "llvm/Support/Error.h"

#include <cstring>
#include <limits>

namespace lldb_private {
class Declaration;
} // namespace lldb_private

using namespace lldb_private;

ValueObjectRecognizedValue::ValueObjectRecognizedValue(
    ValueObject &parent, lldb::DynamicValueType use_dynamic)
    : ValueObject(parent), m_address(), m_dynamic_type_info(),
      m_use_dynamic(use_dynamic) {
  SetName(parent.GetName());
}

CompilerType ValueObjectRecognizedValue::GetCompilerTypeImpl() {
  if (UpdateValueIfNeeded(/*update_format=*/false)) {
    if (m_dynamic_type_info.HasType()) {
      assert(GetValueIsValid());
      return m_value.GetCompilerType();
    }
    return m_parent->GetCompilerType();
  }
  return m_parent->GetCompilerType();
}

ConstString ValueObjectRecognizedValue::GetTypeName() {
  if (UpdateValueIfNeeded(/*update_format=*/false) &&
      m_dynamic_type_info.HasName()) {
    return m_dynamic_type_info.GetName();
  }
  return m_parent->GetTypeName();
}

TypeImpl ValueObjectRecognizedValue::GetTypeImpl() {
  if (UpdateValueIfNeeded(/*update_format=*/false) && m_type_impl.IsValid()) {
    return m_type_impl;
  }
  return m_parent->GetTypeImpl();
}

ConstString ValueObjectRecognizedValue::GetQualifiedTypeName() {
  if (UpdateValueIfNeeded(/*update_format=*/false) &&
      m_dynamic_type_info.HasName()) {
    return m_dynamic_type_info.GetName();
  }
  return m_parent->GetQualifiedTypeName();
}

ConstString ValueObjectRecognizedValue::GetDisplayTypeName() {
  if (UpdateValueIfNeeded(/*update_format=*/false)) {
    if (m_dynamic_type_info.HasType())
      return GetCompilerType().GetDisplayTypeName();
    if (m_dynamic_type_info.HasName())
      return m_dynamic_type_info.GetName();
  }
  return m_parent->GetDisplayTypeName();
}

llvm::Expected<uint32_t>
ValueObjectRecognizedValue::CalculateNumChildren(uint32_t max) {
  if (UpdateValueIfNeeded(/*update_format=*/false) &&
      m_dynamic_type_info.HasType()) {
    ExecutionContext exe_ctx(GetExecutionContextRef());
    llvm::Expected<uint32_t> children_count =
        GetCompilerType().GetNumChildren(true, &exe_ctx);
    if (!children_count)
      return children_count;
    return *children_count <= max ? *children_count : max;
  }
  return m_parent->GetNumChildren(max);
}

llvm::Expected<uint64_t> ValueObjectRecognizedValue::GetByteSize() {
  Status err;
  if (UpdateValueIfNeeded(/*update_format=*/false) &&
      m_dynamic_type_info.HasType()) {
    ExecutionContext exe_ctx(GetExecutionContextRef());
    assert(GetValueIsValid());
    uint64_t byte_size = m_value.GetValueByteSize(&err, &exe_ctx);
    if (err.Fail()) {
      return err.takeError();
    }
    return byte_size;
  }
  return m_parent->GetByteSize();
}

lldb::ValueType ValueObjectRecognizedValue::GetValueType() const {
  return m_parent->GetValueType();
}

bool ValueObjectRecognizedValue::UpdateValue() {
  SetValueIsValid(false);
  m_error.Clear();

  if (!m_parent->UpdateValueIfNeeded(/*update_format=*/false)) {
    if (m_error.Success() && m_parent->GetError().Fail())
      m_error = m_parent->GetError().Clone();
    return false;
  }

  // Clearing m_dynamic_type_info will route everything back through our parent,
  // which is equivalent to not using dynamic value.
  if (m_use_dynamic == lldb::eNoDynamicValues) {
    m_dynamic_type_info.Clear();
    return true;
  }

  ExecutionContext exe_ctx(GetExecutionContextRef());
  Target *target = exe_ctx.GetTargetPtr();
  assert(target);

  m_data.SetByteOrder(target->GetArchitecture().GetByteOrder());
  m_data.SetAddressByteSize(target->GetArchitecture().GetAddressByteSize());

  CompilerType recognized_ct;
  Address dynamic_address;
  lldb::TypeRecognizerImplSP recognizer_sp = m_parent->GetTypeRecognizer();
  assert(recognizer_sp);
  m_error = recognizer_sp->RecognizeObjectType(m_parent, recognized_ct,
                                               dynamic_address);

  if (m_error.Success() && recognized_ct && recognized_ct.IsValid()) {
    if (recognized_ct != this->GetCompilerType()) {
      ClearDynamicTypeInformation();
      SetValueDidChange(true);

      m_type_impl = TypeImpl(m_parent->GetCompilerType(), recognized_ct);
      m_dynamic_type_info.SetCompilerType(recognized_ct);

      if (!m_address.IsValid() || m_address != dynamic_address) {
        m_address = dynamic_address;
        m_value.GetScalar() = m_address.GetLoadAddress(target);
      }

      m_value.SetCompilerType(recognized_ct);
      m_value.SetValueType(Value::ValueType::Scalar);

      m_error = m_value.GetValueAsData(&exe_ctx, m_data, GetModule().get());
      if (!m_error.Success()) {
        SetValueIsValid(false);
        return false;
      }

      Log *log = GetLog(LLDBLog::Types);
      LLDB_LOGF(log, "[%s %p] has new dynamic type %s", GetName().GetCString(),
                static_cast<void *>(this), GetTypeName().GetCString());

      SetValueIsValid(true);
      return true;
    }
  }

  if (m_error.Fail()) {
    target->GetDebugger().GetAsyncErrorStream()->Printf(
        "[%s 0x%016tx] Cast ERROR: %s\n", GetName().GetCString(),
        m_parent->GetPointerValue().address, m_error.AsCString());
  }

  SetValueIsValid(false);
  return false;
}

bool ValueObjectRecognizedValue::IsInScope() { return m_parent->IsInScope(); }

bool ValueObjectRecognizedValue::SetValueFromCString(const char *value_str,
                                                     Status &error) {
  if (!UpdateValueIfNeeded(/*update_format=*/false)) {
    error = m_error.Clone();
    return false;
  }

  uint64_t my_value = GetValueAsUnsigned(std::numeric_limits<uint64_t>::max());
  uint64_t parent_value =
      m_parent->GetValueAsUnsigned(std::numeric_limits<uint64_t>::max());

  if (my_value == std::numeric_limits<uint64_t>::max() ||
      parent_value == std::numeric_limits<uint64_t>::max()) {
    error.FromErrorString("This ValueObject is not in a writteble state");
    return false;
  }

  // if we are at an offset from our parent, in order to set ourselves
  // correctly we would need to change the new value so that it refers to the
  // correct dynamic type. we choose not to deal with that - if anything more
  // than a value overwrite is required, you should be using the expression
  // parser instead of the value editing facility
  if (my_value != parent_value) {
    // but NULL'ing out a value should always be allowed
    if (strcmp(value_str, "0")) {
      error.FromErrorString(
          "unable to modify dynamic value, use 'expression' command");
      return false;
    }
  }

  bool parent_value_was_changed =
      m_parent->SetValueFromCString(value_str, error);
  if (parent_value_was_changed)
    SetNeedsUpdate();

  return parent_value_was_changed;
}

bool ValueObjectRecognizedValue::SetData(DataExtractor &data, Status &error) {
  if (!UpdateValueIfNeeded(/*update_format=*/false)) {
    error.FromErrorString("unable to read value");
    return false;
  }

  uint64_t my_value = GetValueAsUnsigned(std::numeric_limits<uint64_t>::max());
  uint64_t parent_value =
      m_parent->GetValueAsUnsigned(std::numeric_limits<uint64_t>::max());

  if (my_value == std::numeric_limits<uint64_t>::max() ||
      parent_value == std::numeric_limits<uint64_t>::max()) {
    error.FromErrorString("unable to read value");
    return false;
  }

  // if we are at an offset from our parent, in order to set ourselves
  // correctly we would need to change the new value so that it refers to the
  // correct dynamic type. we choose not to deal with that - if anything more
  // than a value overwrite is required, you should be using the expression
  // parser instead of the value editing facility
  if (my_value != parent_value) {
    // but NULL'ing out a value should always be allowed
    lldb::offset_t offset = 0;

    if (data.GetAddress(&offset) != 0) {
      error.FromErrorString(
          "unable to modify dynamic value, use 'expression' command");
      return false;
    }
  }

  bool parent_value_was_changed = m_parent->SetData(data, error);
  if (parent_value_was_changed)
    SetNeedsUpdate();

  return parent_value_was_changed;
}

void ValueObjectRecognizedValue::SetPreferredDisplayLanguage(
    lldb::LanguageType lang) {
  this->ValueObject::SetPreferredDisplayLanguage(lang);
  assert(m_parent);
  m_parent->SetPreferredDisplayLanguage(lang);
}

lldb::LanguageType ValueObjectRecognizedValue::GetPreferredDisplayLanguage() {
  if (m_preferred_display_language == lldb::eLanguageTypeUnknown) {
    assert(m_parent);
    return m_parent->GetPreferredDisplayLanguage();
  }
  return m_preferred_display_language;
}

bool ValueObjectRecognizedValue::IsSyntheticChildrenGenerated() {
  assert(m_parent);
  return m_parent->IsSyntheticChildrenGenerated();
}

void ValueObjectRecognizedValue::SetSyntheticChildrenGenerated(bool value) {
  assert(m_parent);
  m_parent->SetSyntheticChildrenGenerated(value);
}

bool ValueObjectRecognizedValue::GetDeclaration(Declaration &decl) {
  assert(m_parent);
  return m_parent->GetDeclaration(decl);
}

uint64_t ValueObjectRecognizedValue::GetLanguageFlags() {
  assert(m_parent);
  return m_parent->GetLanguageFlags();
}

void ValueObjectRecognizedValue::SetLanguageFlags(uint64_t flags) {
  assert(m_parent);
  m_parent->SetLanguageFlags(flags);
}
