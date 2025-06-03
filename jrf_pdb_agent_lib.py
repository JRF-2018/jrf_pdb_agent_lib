# jrf_pdb_agent_lib.py
__version__ = '0.0.19' # Time-stamp: <2025-06-03T09:00:04Z>

import pdb
import sys
import os
import importlib
import socket # No longer used for send/receive, but kept for potential future use or context
import pickle
import threading
import time
import traceback
import struct # No longer used for send/receive, but kept for potential future use or context
from multiprocessing import shared_memory, resource_tracker

# Global variables for AI interaction.
# These are intended to be set by the AI agent via direct PDB interaction
# or via shared memory, and then acted upon by the program after exiting the debugger.

# EXEC: A string of Python code to be executed in the caller's context
# after the debugger session concludes.
EXEC = None
# RESULT: A value to be returned by the pal.do function to its caller
# after the debugger session concludes.
RESULT = None
# EXCEPTION: A value to be raised by the pal.do function
# after the debugger session concludes.
EXCEPTION = None

# --- Shared Memory Configuration ---
# Dictionary to keep track of active shared memory segments.
# Stores (SharedMemory object, size_of_data_in_bytes) for each identifier.
_shared_memory_segments = {}
# A lock to ensure thread-safe access to the shared memory segments dictionary.
_shared_memory_lock = threading.Lock()

# --- Custom Exception Classes ---

class AiException(Exception):
    """
    Custom exception to be raised by the AI agent or within
    AI-provided code.  This exception is intended to be explicitly
    caught by the AI's logic or the program's error handling. If not
    caught, it will pass through `pal.do` and propagate up the call
    stack, similar to standard Python exceptions.
    """
    pass

class LoopRequestException(Exception):
    """
    Custom exception used by the AI agent within an `EXEC` block
    to explicitly request another iteration of the `EXEC` loop in `pal.do`.

    When this exception is raised by AI-provided code, the current `EXEC`
    block is considered complete, and the debugger session will be re-entered
    to allow the AI to provide the next `EXEC` command, effectively looping.
    This helps in managing multi-step operations within a single `pal.do`
    call without returning control to the main program loop.
    """
    pass

# --- Public Module Functions ---

def login(address_hint=None):
    """
    Initializes the PDB Agent Lib.
    With shared memory as the primary IPC in this version, this function primarily serves
    as a conceptual initialization point. The `address_hint` is not directly used for
    socket binding but can be used for logging or future complex setup.

    Future Considerations:
    If the AI agent operates in a different process or on a different machine, this function
    should be responsible for establishing network IPC connections (e.g., TCP/IP sockets)
    to start a session with the AI agent server. `address_hint` would then serve as the
    connection address for the AI agent.
    """
    print(f"PDB Agent Lib: Initialized. Shared memory is used for IPC.")
    if address_hint:
        print(f"PDB Agent Lib: Address hint provided: {repr(address_hint)} (not used for socket binding in this version).")

def do(order: str, current_code: str = None):
    """
    The core function of the PDB Agent Lib.
    It breaks into the Python debugger (pdb), effectively pausing the program
    and transferring control to the AI agent.

    After the debugger session, it checks the global `EXEC`, `RESULT`
    and 'EXCEPTION' variables (which are expected to be set by the AI
    via direct PDB commands or shared memory interactions) to either
    execute code in the caller's context or return a value.

    Args:
        order (str): A descriptive string outlining the task or instruction
                     for the AI agent. This is displayed when entering pdb.
        current_code (str, optional): An optional string representing the
                                      current code snippet or context that
                                      might be relevant for the AI's decision-making.
                                      This is for AI reference only and not
                                      directly executed by `pal.do`.
    Returns:
        Any: The value set in `pal.RESULT` by the AI, or None if `pal.RESULT`
             was not set.

    """
    global EXEC, RESULT, EXCEPTION

    if sys.gettrace():
        raise RuntimeError("PDB Agent Lib: pal.do is called while debugger is already active.")

    print(f"\n--- PDB Agent Lib: AI Interaction Point ---")
    print(f"Order for AI: {repr(order)}")
    if current_code:
        print(f"Current Code Context (for AI reference): {repr(current_code)}")
    print(f"AI should interact directly via PDB commands or shared memory.")
    print(f"--- PDB Agent Lib: Entering Debugger ---")

    # Reset EXEC, RESULT and EXCEPTION before entering pdb to ensure a
    # clean state for the AI's interaction.
    EXEC = current_code
    RESULT = None
    EXCEPTION = None

    # Get the caller's frame. sys._getframe(1) refers to the frame of the
    # function that called `pal.do`. This allows `exec` to run code
    # in the context where `pal.do` was called.
    frame = sys._getframe(1)
    context_locals = frame.f_locals
    context_globals = frame.f_globals

    # Enter the Python debugger. Program execution pauses here.  The
    # AI agent is expected to interact with the program's state,
    # potentially setting EXEC, RESULT or EXCEPTION directly in PDB or
    # via shared memory.
    pdb.set_trace()

    print(f"--- PDB Agent Lib: Exiting Debugger ---")

    # While the AI has set the global EXEC variable, execute its content.
    while EXEC is not None and EXCEPTION is None:
        print(f"PDB Agent Lib: Executing code from AI: {repr(EXEC)}")
        current_exec = EXEC # Store current EXEC for error reporting
        try:
            # Execute the code string in the caller's local and global context.
            exec(EXEC, context_globals, context_locals)
            print("PDB Agent Lib: AI-provided code execution successful.")
            EXEC = None
        except AiException as e:
            # Handle AiException: This specific exception is intended to
            # immediately signal a controlled error condition to the caller.
            # It breaks the EXEC loop and sets the EXCEPTION global to be raised
            # after the loop concludes.
            print(f"--- PDB Agent Lib: AiException caught during EXEC execution ---")
            print(f"Failing order: {repr(order)}") # Show the order that caused the exception
            print(f"Failing EXEC command: {repr(current_exec)}") # Show the EXEC command that caused the exception
            print(f"--- PDB Agent Lib: Exception set for propagation ---")
            EXEC = None
            EXCEPTION = e
        except Exception as e:
            if isinstance(e, LoopRequestException):
                # If a LoopRequestException is caught, it means the AI
                # explicitly wants to continue the EXEC loop. The EXEC
                # variable is NOT cleared, allowing the while loop to
                # re-evaluate and prompt for the next command.
                print(f"--- PDB Agent Lib: LoopRequestException caught. Requesting next EXEC command. ---")
            else:
                # For any other unexpected exception during EXEC
                # execution, print the error, clear EXEC and
                # EXCEPTION, and re-enter PDB.  This gives the
                # AI/human a chance to inspect the state and fix the
                # issue.
                #
                # Normally, the AI should handle all exceptions and
                # throw an AiException by EXCEPTION only when necessary.
                print(f"--- PDB Agent Lib: Unhandled error during AI-provided code execution ---")
                print(f"Failing EXEC command: {repr(current_exec)}") # Show the EXEC command that caused the exception
                traceback.print_exc() # Print full traceback for debugging
            EXEC = None
            EXCEPTION = None
            pdb.set_trace()
            print(f"--- PDB Agent Lib: Exiting Debugger ---")

    print(f"--- PDB Agent Lib: Exiting AI Interaction ---")

    # After the EXEC loop (either completed, errored, or AiException caught),
    # check for a pending exception to raise.
    if EXCEPTION is not None:
        print(f"PDB Agent Lib: Raising exception from AI.")
        raising_exception = EXCEPTION
        # Clear EXCEPTION after raising to prevent accidental re-use.
        EXCEPTION = None
        raise raising_exception

    # If the AI has set the global RESULT variable, return its value.
    if RESULT is not None:
        print(f"PDB Agent Lib: Returning result from AI.")
        returned_result = RESULT
        # Clear RESULT after returning to prevent accidental re-use.
        RESULT = None
        return returned_result
    else:
        print(f"PDB Agent Lib: No result returned from AI.")
        return None

def consult_human(order: str = None, current_code: str = None):
    """
    A conceptual function for the AI to explicitly request human
    intervention or input. It breaks into the Python debugger,
    signaling that human attention is required. This function
    also handles iterative execution of AI-provided code within the
    human consultation session, similar to `pal.do`.

    Args:
        order (str): A descriptive string outlining the task or
                     instruction for the human or the AI. This is
                     displayed when entering pdb.
        current_code (str, optional): An optional string representing
                                       the current code snippet or
                                       context that might be relevant
                                       for the human's decision-making.

    """
    global EXEC, RESULT, EXCEPTION

    if sys.gettrace():
        raise RuntimeError("PDB Agent Lib: pal.consult_human is called while debugger is already active.")

    print(f"\n--- PDB Agent Lib: Human Consultation Requested ---")
    if order:
        print(f"AI or Human requests: {repr(order)}")
    if current_code:
        print(f"Current Code Context (for Human Reference): {repr(current_code)}")
    print(f"AI should provide input or guidance to the human.")
    print(f"--- PDB Agent Lib: Entering Debugger ---")

    # Reset EXEC, RESULT and EXCEPTION before entering pdb to ensure a
    # clean state for the AI's interaction.
    EXEC = current_code
    RESULT = None
    EXCEPTION = None

    # Get the caller's frame. sys._getframe(1) refers to the frame of the
    # function that called `pal.consult_human`. This allows `exec` to run code
    # in the context where `pal.consult_human` was called.
    frame = sys._getframe(1)
    context_locals = frame.f_locals
    context_globals = frame.f_globals

    # Enter the Python debugger. Program execution pauses here.  The
    # AI agent is expected to interact with the program's state,
    # potentially setting EXEC, RESULT or EXCEPTION directly in PDB or
    # via shared memory.
    pdb.set_trace()
    print(f"--- PDB Agent Lib: Exiting Debugger ---")

    # Loop to execute AI-provided code (via EXEC global) as long as
    # EXEC is set and no exception is signaled. This allows the AI
    # (or human) to run multiple commands iteratively without
    # completely exiting the consultation.
    while EXEC is not None and EXCEPTION is None:
        print(f"PDB Agent Lib: Executing code from AI: {repr(EXEC)}")
        current_exec = EXEC # Store current EXEC for error reporting
        try:
            # Execute the code string in the caller's local and global context.
            exec(EXEC, context_globals, context_locals)
            print("--- PDB Agent Lib: AI-provided code execution successful ---")
            EXEC = None
            pdb.set_trace()
            print(f"--- PDB Agent Lib: Exiting Debugger ---")
        except Exception as e:
            print(f"--- PDB Agent Lib: Error during AI-provided code execution ---")
            print(f"Failing EXEC command: {repr(current_exec)}") # Show the EXEC command that caused the exception
            traceback.print_exc()
            EXEC = None
            EXCEPTION = None
            pdb.set_trace()
            print(f"--- PDB Agent Lib: Exiting Debugger ---")

    print(f"--- PDB Agent Lib: Exiting Human Consultation ---")

    # If the AI has set the global EXCEPTION variable, raise its value.
    if EXCEPTION is not None:
        print(f"PDB Agent Lib: Raising exception from human consultation.")
        raising_exception = EXCEPTION
        # Clear EXCEPTION after raising to prevent accidental re-use.
        EXCEPTION = None
        raise raising_exception

    # If the AI has set the global RESULT variable, return its value.
    if RESULT is not None:
        print(f"PDB Agent Lib: Returning result human consultation.")
        returned_result = RESULT
        # Clear RESULT after returning to prevent accidental re-use.
        RESULT = None
        return returned_result
    else:
        print(f"PDB Agent Lib: No result returned human consultation.")
        return None

def reload_module(module_name: str):
    """
    Loads or reloads a specified Python module.
    This function is primarily intended to be called by the AI agent
    from within the debugger session (or via shared memory command) to apply
    changes to a module dynamically or load a new one without restarting the entire program.

    Args:
        module_name (str): The full name of the module to load or reload (e.g., 'my_module').
    """
    try:
        if module_name in sys.modules:
            # If the module is already loaded, reload it.
            module = sys.modules[module_name]
            importlib.reload(module)
            print(f"PDB Agent Lib: Module '{module_name}' reloaded successfully.")
        else:
            # If the module is not loaded, import it.
            importlib.import_module(module_name)
            print(f"PDB Agent Lib: Module '{module_name}' loaded successfully.")
    except ImportError as e:
        print(f"PDB Agent Lib: Error importing module '{module_name}': {e}")
    except Exception as e:
        print(f"PDB Agent Lib: An unexpected error occurred with module '{module_name}': {e}")

def share_memory(data_identifier: str, data):
    """
    Shares Python `data` using `multiprocessing.shared_memory`.
    The data is first pickled into bytes and then written to a shared memory segment.
    If a segment with `data_identifier` already exists and is too small, it's
    unlinked and recreated with a larger size.

    Args:
        data_identifier (str): A unique string identifier that names the
                               shared memory segment. This name can be used
                               by other processes to attach to the same segment.
        data: The Python object to be shared. This object will be pickled.
    """
    with _shared_memory_lock: # Ensure thread-safe access to shared memory operations.
        try:
            pickled_data = pickle.dumps(data)
            data_size = len(pickled_data)

            shm = None
            if data_identifier in _shared_memory_segments:
                # If segment is already managed by this process, check its size.
                existing_shm, current_size = _shared_memory_segments[data_identifier]
                if current_size < data_size:
                    # If existing segment is too small, close and unlink it.
                    existing_shm.close()
                    existing_shm.unlink()
                    del _shared_memory_segments[data_identifier]
                    print(f"PDB Agent Lib: Resizing shared memory segment '{data_identifier}'.")
                    # Create a new, larger segment.
                    shm = shared_memory.SharedMemory(create=True, size=data_size, name=data_identifier)
                else:
                    # Existing segment is large enough, reuse it.
                    shm = existing_shm
                    print(f"PDB Agent Lib: Using existing shared memory segment '{data_identifier}'.")
            else:
                try:
                    # Try to create a new segment. If it exists, FileExistsError is raised.
                    print(f"PDB Agent Lib: Creating new shared memory segment '{data_identifier}' with size {data_size}.")
                    shm = shared_memory.SharedMemory(create=True, size=data_size, name=data_identifier)
                except FileExistsError:
                    # If it already exists (e.g., created by another process), attach to it.
                    print(f"PDB Agent Lib: Shared memory segment '{data_identifier}' already exists, attaching.")
                    shm = shared_memory.SharedMemory(name=data_identifier)
                    if shm.size < data_size:
                        # If attached segment is too small, this is a problem.
                        # In a real system, you'd need a more robust negotiation or error.
                        # For this concept, we'll just print a warning.
                        print(f"PDB Agent Lib: WARNING: Attached shared memory segment '{data_identifier}' is too small ({shm.size} < {data_size}). Data might be truncated.")
                        # A proper solution would involve IPC to tell the creator to resize.

            if shm:
                # Copy the pickled data into the shared memory buffer.
                shm.buf[:data_size] = pickled_data
                _shared_memory_segments[data_identifier] = (shm, data_size)
                print(f"PDB Agent Lib: Data shared to '{data_identifier}'.")

        except Exception as e:
            print(f"PDB Agent Lib: Error sharing memory for '{data_identifier}': {e}")

def retrieve_shared_memory(data_identifier: str):
    """
    Retrieves and deserializes data from a `multiprocessing.shared_memory` segment.

    Args:
        data_identifier (str): The unique string identifier of the shared memory segment.

    Returns:
        Any: The deserialized Python object, or None if the segment is not found
             or an error occurs during retrieval/deserialization.
    """
    with _shared_memory_lock: # Ensure thread-safe access.
        shm = None
        size = 0
        if data_identifier in _shared_memory_segments:
            shm, size = _shared_memory_segments[data_identifier]
        else:
            try:
                # Try to attach to an existing segment if not managed by this process.
                shm = shared_memory.SharedMemory(name=data_identifier)
                # If successfully attached, store it for future use.
                size = shm.size # Assume the entire segment contains valid data for simplicity.
                _shared_memory_segments[data_identifier] = (shm, size)
                print(f"PDB Agent Lib: Attached to existing shared memory segment '{data_identifier}'.")
            except FileNotFoundError:
                print(f"PDB Agent Lib: Shared memory segment '{data_identifier}' not found.")
                return None
            except Exception as e:
                print(f"PDB Agent Lib: Error attaching to shared memory '{data_identifier}': {e}")
                return None

        if shm:
            try:
                # Read the data from the shared memory buffer.
                # Note: This assumes the 'size' stored or retrieved from shm.size
                # accurately reflects the length of the pickled data.
                # A more robust system would store the actual data length within
                # the shared memory itself or communicate it via IPC.
                pickled_data = bytes(shm.buf[:size])
                data = pickle.loads(pickled_data)
                print(f"PDB Agent Lib: Data retrieved from '{data_identifier}'.")
                return data
            except Exception as e:
                print(f"PDB Agent Lib: Error retrieving data from shared memory '{data_identifier}': {e}")
                return None
        return None

def send(data_identifier: str, data):
    """
    Sends data using shared memory. This function is currently an alias for `share_memory`.
    It writes data to a shared memory segment, which can then be read by another
    process (e.g., the AI agent) that knows the `data_identifier`.

    Args:
        data_identifier (str): A unique string identifier for the shared memory segment.
        data: The Python object to be sent. It will be pickled.

    Future Considerations:
    If the AI agent operates in a different process or on a different machine, this function
    should be responsible for sending data to the AI agent's specific IPC endpoint
    (e.g., via TCP/IP sockets). It would use a more general IPC mechanism instead of shared memory.
    """
    print(f"PDB Agent Lib: Sending data '{data_identifier}' via shared memory.")
    share_memory(data_identifier, data)

def receive(data_identifier: str):
    """
    Receives data using shared memory. This function is currently an alias for `retrieve_shared_memory`.
    It reads data from a shared memory segment identified by `data_identifier`.

    Args:
        data_identifier (str): The unique string identifier for the shared memory segment.

    Returns:
        Any: The deserialized Python object, or None if the segment is not found
             or an error occurs during retrieval/deserialization.

    Future Considerations:
    If the AI agent operates in a different process or on a different machine, this function
    should be responsible for receiving data from the AI agent's specific IPC endpoint
    (e.g., via TCP/IP sockets). It would use a more general IPC mechanism instead of shared memory.
    """
    print(f"PDB Agent Lib: Attempting to receive data '{data_identifier}' via shared memory.")
    return retrieve_shared_memory(data_identifier)

def preserve_full_context(filename="context_snapshot.pkl"):
    """
    Attempts to preserve the full local and global context of the caller's frame
    by pickling them to a specified file.

    WARNING: This is a highly conceptual and limited implementation.
    Pickling Python frames and their full context (including closures,
    module references, and complex object graphs) is notoriously difficult
    and often leads to `PicklingError` or unexpected behavior upon restoration.
    It is NOT a true `callcc` (call with current continuation) equivalent,
    which would require deep runtime state capture and restoration.

    Args:
        filename (str): The file path where the context snapshot will be saved.
    """
    try:
        # Get the caller's frame.
        frame = sys._getframe(1)
        # Create a dictionary to store local and global variables.
        # We filter out built-in variables and callables to reduce complexity
        # and potential pickling errors, but this makes the "full" context
        # preservation incomplete.
        context = {
            'locals': {k: v for k, v in frame.f_locals.items() if not k.startswith('__')},
            'globals': {k: v for k, v in frame.f_globals.items() if not k.startswith('__') and not callable(v)},
        }
        # Save the context to a file using pickle.
        with open(filename, 'wb') as f:
            pickle.dump(context, f)
        print(f"PDB Agent Lib: Context snapshot saved to '{filename}'.")
    except Exception as e:
        print(f"PDB Agent Lib: Error preserving context: {e}")
        print("PDB Agent Lib: This feature is highly experimental and limited in Python.")

def restore_full_context(filename="context_snapshot.pkl"):
    """
    Attempts to restore a previously preserved context from a file.

    WARNING: This is a highly conceptual and limited implementation.
    Restoring Python context perfectly is extremely difficult and often problematic,
    especially with complex object references and module states.
    It is NOT a true `callcc` (call with current continuation) equivalent.

    Args:
        filename (str): The file path from which the context snapshot will be loaded.
    """
    try:
        # Load the context from the file.
        with open(filename, 'rb') as f:
            context = pickle.load(f)

        # Get the caller's frame to apply the restored context.
        frame = sys._getframe(1)
        # Restore local variables.
        for k, v in context['locals'].items():
            frame.f_locals[k] = v
        # Restore global variables. Be cautious not to overwrite essential
        # modules or built-in functions, as this can lead to program instability.
        for k, v in context['globals'].items():
            # Only restore if the global variable is not a loaded module or a built-in.
            if k not in sys.modules and k not in __builtins__:
                frame.f_globals[k] = v

        print(f"PDB Agent Lib: Context snapshot loaded from '{filename}'.")
        print("PDB Agent Lib: Context restoration is highly experimental and limited.")
    except FileNotFoundError:
        print(f"PDB Agent Lib: Context snapshot file '{filename}' not found.")
    except Exception as e:
        print(f"PDB Agent Lib: Error restoring context: {e}")
        print("PDB Agent Lib: This feature is highly experimental and limited in Python.")

# --- Cleanup for Shared Memory Segments ---
# It's crucial to unlink shared memory segments when they are no longer needed
# to prevent resource leaks, especially across different processes.
# The `atexit` module is used to register a cleanup function that runs
# automatically when the program exits.

def _cleanup_shared_memory():
    """
    Unlinks all shared memory segments that were created or attached to by
    this process. This ensures that the underlying system resources are
    released.
    """
    with _shared_memory_lock:
        # Iterate over a copy of the dictionary to allow modification during iteration.
        for name, (shm, _) in list(_shared_memory_segments.items()):
            try:
                shm.close() # Close the SharedMemory object.
                shm.unlink() # Unlink the shared memory segment from the system.
                print(f"PDB Agent Lib: Unlinked shared memory segment '{name}'.")
            except FileNotFoundError:
                # This can happen if another process already unlinked it.
                pass
            except Exception as e:
                print(f"PDB Agent Lib: Error unlinking shared memory segment '{name}': {e}")
            finally:
                # Remove the segment from our internal tracking dictionary.
                del _shared_memory_segments[name]

# Register the cleanup function to be called automatically upon program termination.
import atexit
atexit.register(_cleanup_shared_memory)

