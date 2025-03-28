//===--- Analysis.h - Analyze symbol references in AST ------------- C++-*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
/// A library that provides usage analysis for symbols based on AST analysis.
//===----------------------------------------------------------------------===//

#ifndef CLANG_INCLUDE_CLEANER_ANALYSIS_H
#define CLANG_INCLUDE_CLEANER_ANALYSIS_H

#include "clang-include-cleaner/Record.h"
#include "clang-include-cleaner/Types.h"
#include "clang/Format/Format.h"
#include "clang/Lex/HeaderSearch.h"
#include "clang/Lex/Preprocessor.h"
#include "llvm/ADT/ArrayRef.h"
#include "llvm/ADT/STLFunctionalExtras.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/ADT/StringRef.h"
#include <string>
#include <utility>

namespace clang {
class SourceLocation;
class SourceManager;
class Decl;
class FileEntry;
class HeaderSearch;
namespace tooling {
class Replacements;
struct IncludeStyle;
} // namespace tooling
namespace include_cleaner {

/// A UsedSymbolCB is a callback invoked for each symbol reference seen.
///
/// References occur at a particular location, refer to a single symbol, and
/// that symbol may be provided by several headers.
/// FIXME: Provide signals about the providing headers so the caller can filter
/// and rank the results.
using UsedSymbolCB = llvm::function_ref<void(const SymbolReference &SymRef,
                                             llvm::ArrayRef<Header> Providers)>;

/// Find and report all references to symbols in a region of code.
/// It only reports references from main file.
///
/// The AST traversal is rooted at ASTRoots - typically top-level declarations
/// of a single source file.
/// The references to macros must be recorded separately and provided.
///
/// This is the main entrypoint of the include-cleaner library, and can be used:
///  - to diagnose missing includes: a referenced symbol is provided by
///    headers which don't match any #include in the main file
///  - to diagnose unused includes: an #include in the main file does not match
///    the headers for any referenced symbol
void walkUsed(llvm::ArrayRef<Decl *> ASTRoots,
              llvm::ArrayRef<SymbolReference> MacroRefs,
              const PragmaIncludes *PI, const Preprocessor &PP,
              UsedSymbolCB CB);

struct AnalysisResults {
  std::vector<const Include *> Unused;
  // Spellings, like "<vector>" paired with the Header that generated it.
  std::vector<std::pair<std::string, Header>> Missing;
};

/// Determine which headers should be inserted or removed from the main file.
/// This exposes conclusions but not reasons: use lower-level walkUsed for that.
///
/// The HeaderFilter is a predicate that receives absolute path or spelling
/// without quotes/brackets, when a phyiscal file doesn't exist.
/// No analysis will be performed for headers that satisfy the predicate.
AnalysisResults
analyze(llvm::ArrayRef<Decl *> ASTRoots,
        llvm::ArrayRef<SymbolReference> MacroRefs, const Includes &I,
        const PragmaIncludes *PI, const Preprocessor &PP,
        llvm::function_ref<bool(llvm::StringRef)> HeaderFilter = nullptr);

/// Removes unused includes and inserts missing ones in the main file.
/// Returns the modified main-file code.
/// The FormatStyle must be C++ or ObjC (to support include ordering).
std::string fixIncludes(const AnalysisResults &Results,
                        llvm::StringRef FileName, llvm::StringRef Code,
                        const format::FormatStyle &IncludeStyle);

/// Gets all the providers for a symbol by traversing each location.
/// Returned headers are sorted by relevance, first element is the most
/// likely provider for the symbol.
llvm::SmallVector<Header> headersForSymbol(const Symbol &S,
                                           const Preprocessor &PP,
                                           const PragmaIncludes *PI);
} // namespace include_cleaner
} // namespace clang

#endif
