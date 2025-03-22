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
#include "lldb/lldb-types.h"

#include "llvm/Support/Error.h"

#include <cstring>

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
  const bool success = UpdateValueIfNeeded(false);
  if (success) {
    if (m_dynamic_type_info.HasType())
      return m_value.GetCompilerType();
    return m_parent->GetCompilerType();
  }
  return m_parent->GetCompilerType();
}

ConstString ValueObjectRecognizedValue::GetTypeName() {
  const bool success = UpdateValueIfNeeded(false);
  if (success) {
    if (m_dynamic_type_info.HasName())
      return m_dynamic_type_info.GetName();
  }
  return m_parent->GetTypeName();
}

TypeImpl ValueObjectRecognizedValue::GetTypeImpl() {
  const bool success = UpdateValueIfNeeded(false);
  if (success && m_type_impl.IsValid()) {
    return m_type_impl;
  }
  return m_parent->GetTypeImpl();
}

ConstString ValueObjectRecognizedValue::GetQualifiedTypeName() {
  const bool success = UpdateValueIfNeeded(false);
  if (success) {
    if (m_dynamic_type_info.HasName())
      return m_dynamic_type_info.GetName();
  }
  return m_parent->GetQualifiedTypeName();
}

ConstString ValueObjectRecognizedValue::GetDisplayTypeName() {
  const bool success = UpdateValueIfNeeded(false);
  if (success) {
    if (m_dynamic_type_info.HasType())
      return GetCompilerType().GetDisplayTypeName();
    if (m_dynamic_type_info.HasName())
      return m_dynamic_type_info.GetName();
  }
  return m_parent->GetDisplayTypeName();
}

llvm::Expected<uint32_t>
ValueObjectRecognizedValue::CalculateNumChildren(uint32_t max) {
  const bool success = UpdateValueIfNeeded(false);
  if (success && m_dynamic_type_info.HasType()) {
    ExecutionContext exe_ctx(GetExecutionContextRef());
    auto children_count = GetCompilerType().GetNumChildren(true, &exe_ctx);
    if (!children_count)
      return children_count;
    return *children_count <= max ? *children_count : max;
  }
  return m_parent->GetNumChildren(max);
}

llvm::Expected<uint64_t> ValueObjectRecognizedValue::GetByteSize() {
  const bool success = UpdateValueIfNeeded(false);
  if (success && m_dynamic_type_info.HasType()) {
    ExecutionContext exe_ctx(GetExecutionContextRef());
    return m_value.GetValueByteSize(nullptr, &exe_ctx);
  }
  return m_parent->GetByteSize();
}

lldb::ValueType ValueObjectRecognizedValue::GetValueType() const {
  return m_parent->GetValueType();
}

bool ValueObjectRecognizedValue::UpdateValue() {
  SetValueIsValid(false);
  m_error.Clear();

  if (!m_parent->UpdateValueIfNeeded(false)) {
    // The dynamic value failed to get an error, pass the error along
    if (m_error.Success() && m_parent->GetError().Fail())
      m_error = m_parent->GetError().Clone();
    return false;
  }

  // Setting our type_sp to NULL will route everything back through our parent
  // which is equivalent to not using dynamic values.
  if (m_use_dynamic == lldb::eNoDynamicValues) {
    m_dynamic_type_info.Clear();
    return true;
  }

  ExecutionContext exe_ctx(GetExecutionContextRef());
  Target *target = exe_ctx.GetTargetPtr();
  if (target) {
    m_data.SetByteOrder(target->GetArchitecture().GetByteOrder());
    m_data.SetAddressByteSize(target->GetArchitecture().GetAddressByteSize());
  }

  Value old_value(m_value);

  CompilerType recognized_ct;
  Address dynamic_address;
  m_error = m_parent->GetTypeRecognizer()->RecognizeObjectType(
      m_parent, recognized_ct, dynamic_address);

  if (m_error.Success() && recognized_ct && recognized_ct.IsValid()) {
    if (recognized_ct != this->GetCompilerType()) {
      ClearDynamicTypeInformation();
      SetValueDidChange(true);

      m_type_impl = TypeImpl(m_parent->GetCompilerType(), recognized_ct);
      m_dynamic_type_info.SetCompilerType(recognized_ct);

      if (!m_address.IsValid() || m_address != dynamic_address) {
        if (m_address.IsValid())
          SetValueDidChange(true);

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
      LLDB_LOGF(log, "[%s %p] has a new dynamic type %s",
                GetName().GetCString(), static_cast<void *>(this),
                GetTypeName().GetCString());

      SetValueIsValid(true);
      return true;
    }
  }

  if (m_error.Fail() && target) {
    target->GetDebugger().GetAsyncErrorStream()->Printf(
        "[%s 0x%016tx] Cast ERROR: %s\n", GetName().GetCString(),
        m_parent->GetPointerValue(), m_error.AsCString());
  }

  SetValueIsValid(false);
  return false;
}

bool ValueObjectRecognizedValue::IsInScope() { return m_parent->IsInScope(); }

bool ValueObjectRecognizedValue::SetValueFromCString(const char *value_str,
                                                     Status &error) {
  if (!UpdateValueIfNeeded(false)) {
    error.FromErrorString("unable to read value");
    return false;
  }

  uint64_t my_value = GetValueAsUnsigned(UINT64_MAX);
  uint64_t parent_value = m_parent->GetValueAsUnsigned(UINT64_MAX);

  if (my_value == UINT64_MAX || parent_value == UINT64_MAX) {
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
    if (strcmp(value_str, "0")) {
      error.FromErrorString(
          "unable to modify dynamic value, use 'expression' command");
      return false;
    }
  }

  bool ret_val = m_parent->SetValueFromCString(value_str, error);
  SetNeedsUpdate();
  return ret_val;
}

bool ValueObjectRecognizedValue::SetData(DataExtractor &data, Status &error) {
  if (!UpdateValueIfNeeded(false)) {
    error.FromErrorString("unable to read value");
    return false;
  }

  uint64_t my_value = GetValueAsUnsigned(UINT64_MAX);
  uint64_t parent_value = m_parent->GetValueAsUnsigned(UINT64_MAX);

  if (my_value == UINT64_MAX || parent_value == UINT64_MAX) {
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

  bool ret_val = m_parent->SetData(data, error);
  SetNeedsUpdate();
  return ret_val;
}

void ValueObjectRecognizedValue::SetPreferredDisplayLanguage(
    lldb::LanguageType lang) {
  this->ValueObject::SetPreferredDisplayLanguage(lang);
  if (m_parent)
    m_parent->SetPreferredDisplayLanguage(lang);
}

lldb::LanguageType ValueObjectRecognizedValue::GetPreferredDisplayLanguage() {
  if (m_preferred_display_language == lldb::eLanguageTypeUnknown) {
    if (m_parent)
      return m_parent->GetPreferredDisplayLanguage();
    return lldb::eLanguageTypeUnknown;
  }
  return m_preferred_display_language;
}

bool ValueObjectRecognizedValue::IsSyntheticChildrenGenerated() {
  if (m_parent)
    return m_parent->IsSyntheticChildrenGenerated();
  return false;
}

void ValueObjectRecognizedValue::SetSyntheticChildrenGenerated(bool b) {
  if (m_parent)
    m_parent->SetSyntheticChildrenGenerated(b);
  this->ValueObject::SetSyntheticChildrenGenerated(b);
}

bool ValueObjectRecognizedValue::GetDeclaration(Declaration &decl) {
  if (m_parent)
    return m_parent->GetDeclaration(decl);

  return ValueObject::GetDeclaration(decl);
}

uint64_t ValueObjectRecognizedValue::GetLanguageFlags() {
  if (m_parent)
    return m_parent->GetLanguageFlags();
  return this->ValueObject::GetLanguageFlags();
}

void ValueObjectRecognizedValue::SetLanguageFlags(uint64_t flags) {
  if (m_parent)
    m_parent->SetLanguageFlags(flags);
  else
    this->ValueObject::SetLanguageFlags(flags);
}
