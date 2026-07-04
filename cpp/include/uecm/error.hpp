#pragma once
#include <cstdint>
#include <expected>
#include <string_view>

// Closed error set and result type. See spec/SPECIFICATION.md §6.6.
namespace uecm {

enum class OpError : std::uint8_t {
  NotFound = 0,
  AlreadyExists = 1,
  InvalidState = 2,
  CapacityExceeded = 3,
  InvalidArgument = 4,
};

// OpResult<T> = Ok(T) or Err(OpError). C++23 std::expected.
template <class T>
using OpResult = std::expected<T, OpError>;

constexpr std::string_view to_string(OpError e) noexcept {
  switch (e) {
    case OpError::NotFound:         return "NotFound";
    case OpError::AlreadyExists:    return "AlreadyExists";
    case OpError::InvalidState:     return "InvalidState";
    case OpError::CapacityExceeded: return "CapacityExceeded";
    case OpError::InvalidArgument:  return "InvalidArgument";
  }
  return "Unknown";
}

}  // namespace uecm
