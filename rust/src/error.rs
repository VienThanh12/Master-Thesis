//! Closed error set and result type. See `../spec/SPECIFICATION.md` §6.6.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum OpError {
    NotFound = 0,
    AlreadyExists = 1,
    InvalidState = 2,
    CapacityExceeded = 3,
    InvalidArgument = 4,
}

/// `OpResult<T>` = `Ok(T)` or `Err(OpError)` (spec §6.6).
pub type OpResult<T> = Result<T, OpError>;

impl OpError {
    pub const fn as_str(self) -> &'static str {
        match self {
            OpError::NotFound => "NotFound",
            OpError::AlreadyExists => "AlreadyExists",
            OpError::InvalidState => "InvalidState",
            OpError::CapacityExceeded => "CapacityExceeded",
            OpError::InvalidArgument => "InvalidArgument",
        }
    }
}
