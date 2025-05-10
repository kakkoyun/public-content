![[parca_screenshot.png]]

> Check our [quick start](https://www.parca.dev/docs/quickstart) for more details.

> At Polar Signals, we've prided ourselves on offering first-class support for profiling compiled languages through our open-source

> eBPF-based profiling agent, Parca Agent. Recognizing the increasing use and importance of interpreted languages in modern software development (it's no news that Python is widely used in AI and ML), we decided it was the right time to bring them to the forefront of our profiling capabilities across runtimes. It goes all the way from native code to the kernel and now, interpreted languages too, in one cohesive view.

> But what makes them unique to profile? What are the challenges? How did we do it? Let's dive in!

## The Problem

Profiling interpreted code comes with its unique set of complexities, but similarly to profiling native code, it also requires a deep understanding of the runtime's internals.

> We've written more on our approach for profiling compiled programs without frame-pointers with low overhead: 👉 [DWARF-based Stack Walking Using eBPF](https://www.polarsignals.com/blog/posts/2022/11/29/dwarf-based-stack-walking-using-ebpf)

https://pprof.me/4e5957b/embed/

_Interpreters_ are programs that read and execute code. To understand how they work, we must grasp two key components: _runtimes_ and _abstract stacks_. Runtimes manage the program's lifecycle, including code execution, memory management, and system interaction. Abstract stacks, on the other hand, are data structures used by interpreters to track variables and control flow, facilitating code execution by managing data storage and retrieval.

Profiling code on an interpreter demands navigating through these layers and understanding how high-level code is processed. In its simplest form, this entails finding the data structures holding the virtual machine's state, reading abstract stack data from memory structures, and constructing a stack trace to obtain a complete picture of the program's execution.

## A solution

How can we do this? We need to dive into runtimes' source code. When we check the Python and Ruby source code, we can see that the runtime is implemented in _C_. This means that we can use eBPF to read the abstract stack data from the in-memory structures.

All the runtime data for Python is stored in a struct called `PyRuntimeState`. This struct contains all the information about the runtime, including the abstract stack. Similarly, all the runtime data for Ruby is stored in a struct called `ruby_current_vm`. This struct contains all the information about the runtime, including the abstract stack.

Let's have a look at these structs:

https://github.com/python/cpython/blob/8c071373f12f325c54591fe990ec026184e48f8f/Include/internal/pycore_interp.h#L42-L209

The code is heavily omitted for brevity. You can check the full source code from the links above.
The key takeaway here is that we can use these structs to read the abstract stack data from memory. And by reading some of this data, we can construct a stack trace.

### We need a map 🗺️ to find our way

In order to unwind the abstract stack, we need to understand how the abstract stack is implemented. For example, it can be implemented as a linked list. Each frame in the abstract stack points to the previous frame. This means that we can unwind the abstract stack by following the pointers.

To start unwinding, we need to find the address of the first frame in the abstract stack. This is the frame that is currently executing. We need to unwind the stacks per _thread_. This is because each thread has its own stack. In the code snippets above that belong to runtime structs, we can see that the `PyThreadState` struct contains the abstract stack data. Similarly, in Ruby, the `rb_thread_struct` struct contains the abstract stack data.

Let's have a look at these structs:

https://github.com/python/cpython/blob/2d4865d775123e8889c7a79fc49b4bf627176c4b/Include/cpython/pystate.h#L64-L195

For Python, it is straightforward to find the address of the current frame. Its name is quite obvious!

```c
/* Pointer to currently executing frame. */
struct _PyInterpreterFrame *current_frame;
```

For Ruby, we need to jump one step further and check what we have in `rb_execution_context_t *ec` struct.

Aha, it looks like we found what we are looking for `rb_control_frame_t *cfp;` 🎉

Let's quickly have a look at these structs as well:

https://github.com/python/cpython/blob/4227bfa8b273207a2b882f7d69c8ac49c3d2b57d/Include/internal/pycore_frame.h#L53-L77

Now, we have all the addresses we need to unwind the abstract stack. We can start from the current frame and follow the pointers to the previous frames. We can do this until we reach the end of the abstract stack. The pseudo-code for this would look like this:

```c
while (frame != NULL) {
  // Do something with the frame
  frame = frame->previous_frame;
}
```

All the information above gives us a map to where to look for while the interpreter is running. The next big question is where can we find this information in the memory?

### Where to start?

It all starts with finding where the runtime resides in the memory. The easiest way to do this is to find the binary symbol corresponding to the runtime struct. For example, in Python, this is the `PyRuntimeState` struct. In Ruby, this is the `ruby_current_vm` struct.

A quick reminder: As of now, eBPF is only supported on Linux. So, the following examples are only valid for Linux. As a result, we use [ELF](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format) binaries. That being said, the eBPF support for other operating systems is in the works. e.g [eBPF for Windows](https://github.com/microsoft/ebpf-for-windows).

> For the rest of the blog post, we will use Python as an example. However, the same concepts apply to Ruby as well.

Let's start with finding the `PyRuntimeState` struct in the memory. We can do this by using the `nm` command. This command lists the symbols in the binary. We can use the `grep` command to filter the output. The runtime binary can be statically linked or dynamically linked. In the case of Python, it is dynamically linked. This means that we need to check the symbols in the runtime library. In the case of Python, this is the `libpython3.11.so.1.0` library.

```shell
❯ ldd /usr/bin/python3.11
	linux-vdso.so.1 (0x00007ffeca9e2000)
	libpython3.11.so.1.0 => /usr/lib/libpython3.11.so.1.0 (0x00007fe6eaa00000)
	libc.so.6 => /usr/lib/libc.so.6 (0x00007fe6ea81e000)
	libm.so.6 => /usr/lib/libm.so.6 (0x00007fe6eb06f000)
	/lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x00007fe6eb18e000)
```

The executable linked against the `libpython3.11.so.1.0` library. Let's check the symbols in this library:

```shell
❯ nm /usr/lib/libpython3.11.so.1.0 | grep PyRuntime
0000000000557d20 D _PyRuntime
0000000000297290 T _PyRuntime_Finalize
0000000000297220 T _PyRuntime_Initialize
000000000029a7a0 T _PyRuntimeState_Fini
000000000029a600 T _PyRuntimeState_Init
000000000029a840 t _PyRuntimeState_ReInitThreads
```

Now, we know the relative address of the `PyRuntimeState` struct in the executable section of the binary. We can use this address to read the runtime state from the memory.
However, first we need to find the base address of the executable section in the memory.

```shell
❯ python
Python 3.11.5 (main, Sep  2 2023, 14:16:33) [GCC 13.2.1 20230801] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> process = multiprocessing.current_process()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'multiprocessing' is not defined
>>> import multiprocessing
>>> process = multiprocessing.current_process()
>>> process.pid
18535
```

We can do this by reading the `/proc/<PID>/maps` file. This file contains memory mappings of the process.
Using this file we can check the `libpython3.11.so.1.0` library's base address in memory.

```shell
❯ cat /proc/18535/maps | grep libpython3.11.so.1.0
7f0882a00000-7f0882aee000 r--p 00000000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
7f0882aee000-7f0882d3d000 r-xp 000ee000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
7f0882d3d000-7f0882e2a000 r--p 0033d000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
7f0882e2a000-7f0882e59000 r--p 0042a000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
7f0882e59000-7f0882f89000 rw-p 00459000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
```

And then we calculate the actual address of the `PyRuntimeState` struct in memory. We can do this by adding the relative address of the `PyRuntimeState` struct in the executable section to the base address of the executable section in the memory.

Now, we know where to start. And we have a map to follow. We can start unwinding the stack.
Or can we? Do we know actually how to read the map?

### Reading the map

We have the source code of the runtime, and we know where to look according to the source code. However, the compiled languages are not executed as they are written. They are compiled to machine code. And the machine code is just a bunch of bytes. So, we need to specifically know where to look in the memory. We need to know the exact offsets of the fields in the structs. How can we achive this?

#### Enter GDB

[GDB](https://www.gnu.org/software/gdb/) is a debugger that allows us to inspect any program while it is running.

```text
❯ gdb -p $(pidof python)
GNU gdb (GDB) 13.2
Copyright (C) 2023 Free Software Foundation, Inc.
For help, type "help".
Type "apropos word" to search for commands related to "word".
Attaching to process 273506
```

With GDB, you can seach for a specific symbol and find out where it is located in the memory.
Moreover, when the source code is available, you can pretty print a chunk of memory with its corresponding human-readible names. And you can even find the exact offsets of the fields in the structs. We just need to extend the GDB with a small script.

```text
> macro define offsetof(t, f) &((t *) 0)->f
> p/d offsetof(PyRuntimeState, interp)
$1 = 48 # This is the offset of the `interp` field in the `PyRuntimeState` struct
```

Using this method, we can find the offsets of the fields in the structs. And we can use these offsets to read the structs from the memory. As you can image this is a very tedious process. We need to do this for every field in every struct that we need. And we need to do this for every runtime and its each and every version. GDB is able to understand these C structures thanks to the type information that DWARF provides. While we could have implemented this in our profiler to extract the exact ABI details, such as offsets and sizes of core data structures, this would not work well. First, parsing DWARF is not an easy task and it can consume a non-trivial amount of CPU cycles. The other big issue is that there is no guarantee that the binaries will have DWARF information. It might have been stripped to reduce the binary size. We ad to follow a different approach.

#### Generating type information ahead of time

We have created a project called [parca-dev/runtime-data](https://github.com/parca-dev/runtime-data) which contains the offsets of the fields in the structs for the runtimes. It is automatically generated from the source code of the runtimes. This means that we can use this project to generate the offsets for any runtime and its each and every version. And we can use these offsets to read the structs from the memory. It is using battle-tested [Rust Bindgen](https://github.com/rust-lang/rust-bindgen) to generate the offsets.

However this blog post is already getting longer and we don't have time to dive into details. If you are curious, feel free to dive in and let use know what you think. We are always open to any feedback and contribution.

### Unwinding the stack

Alright, now we have all the information we need to unwind the abstract stack, for sure. Let's unwind the stack!
Do you remember the address we have found for the interpreter state? Let's read the interpreter state from the memory.

> We will demostrate here for only one stack of a single thread. However, we need to do this each and every thread that is running.

```c
LOG("interpreter_info->thread_state_addr 0x%llx", interpreter_info->thread_state_addr);
int err = bpf_probe_read_user(&state->thread_state, sizeof(state->thread_state), (void *)(long)interpreter_info->thread_state_addr);
if (err != 0) {
  LOG("[error] bpf_probe_read_user failed with %d", err);
  goto submit_without_unwinding;
}
LOG("thread_state 0x%llx", state->thread_state);

GET_OFFSETS();

// Get pointer to top frame from PyThreadState.
if (offsets->py_thread_state.frame > -1) {
  LOG("offsets->py_thread_state.frame %d", offsets->py_thread_state.frame);
  bpf_probe_read_user(&state->frame_ptr, sizeof(void *), state->thread_state + offsets->py_thread_state.frame);
}
```

Now that we have a pointer that we can use to start unwinding the stack. We can do this by following the pointers to the previous frames. We have to do this until we reach the end of the abstract stack. A pseudo-code for this would look like this:

```c
for (int i = 0; i < PYTHON_STACK_FRAMES_PER_PROG; i++) {
  void *cur_frame = state->frame_ptr;
  if (!cur_frame) {
    break;
  }

  // Read the code pointer. PyFrameObject.f_code
  void *cur_code_ptr;
  bpf_probe_read_user(&cur_code_ptr, sizeof(cur_code_ptr), state->frame_ptr + offsets->py_frame_object.f_code);
  if (!cur_code_ptr) {
    break;
  }

  u64 cur_len = sample->stack.len;
  if (cur_len >= 0 && cur_len < MAX_STACK_DEPTH) {
    sample->stack.addresses[cur_len] = symbol_id;
    sample->stack.len++;
  }
  frame_count++;

  bpf_probe_read_user(&state->frame_ptr, sizeof(state->frame_ptr), cur_frame + offsets->py_frame_object.f_back);
  if (!state->frame_ptr) {
    // There aren't any frames to read. We are done.
    goto complete;
  }
}
```

#### Reading functions and other names

Let's assume we have all the required offsets. We can use these offsets to read the structs from the memory. Most interpreters include the function name and other metadata directly on the frame, so we need to read that information off that structure.

Back to our unwinding code:

```c
for (int i = 0; i < PYTHON_STACK_FRAMES_PER_PROG; i++) {
  void *cur_frame = state->frame_ptr;

  // ...

  LOG("## frame %d", frame_count);
  LOG("\tcur_frame_ptr 0x%llx", cur_frame);
  LOG("\tcur_code_ptr 0x%llx", cur_code_ptr);

  symbol_t sym = (symbol_t){0};
  // Read symbol information from the code object if possible.
  read_symbol(offsets, cur_frame, cur_code_ptr, &sym);

  LOG("\tsym.path %s", sym.path);
  LOG("\tsym.class_name %s", sym.class_name);
  LOG("\tsym.method_name %s", sym.method_name);
  LOG("\tsym.lineno %d", sym.lineno);

  // ...

  bpf_probe_read_user(&state->frame_ptr, sizeof(state->frame_ptr), cur_frame + offsets->py_frame_object.f_back);
  if (!state->frame_ptr) {
    // There aren't any frames to read. We are done.
    goto complete;
  }
}
```

For each frame we will check corresponding code object. And we will read the symbol information from the code object. Let's have a look at the `read_symbol` function:

```c
static inline __attribute__((__always_inline__))
void read_symbol(PythonVersionOffsets *offsets, void *cur_frame, void *code_ptr, symbol_t *symbol) {
  // ...

  // GDB: $frame->f_localsplus[0]->ob_type->tp_name
  if (first_self || first_cls) {
    void *ptr;
    bpf_probe_read_user(&ptr, sizeof(void *), cur_frame + offsets->py_frame_object.f_localsplus);
    if (first_self) {
      // We are working with an instance, first we need to get type.
      bpf_probe_read_user(&ptr, sizeof(void *), ptr + offsets->py_object.ob_type);
    }
    bpf_probe_read_user(&ptr, sizeof(void *), ptr + offsets->py_type_object.tp_name);
    bpf_probe_read_user_str(&symbol->class_name, sizeof(symbol->class_name), ptr);
  }

  void *pystr_ptr;

  // GDB: $frame->f_code->co_filename
  bpf_probe_read_user(&pystr_ptr, sizeof(void *), code_ptr + offsets->py_code_object.co_filename);
  bpf_probe_read_user_str(&symbol->path, sizeof(symbol->path), pystr_ptr + offsets->py_string.data);

  // GDB: $frame->f_code->co_name
  bpf_probe_read_user(&pystr_ptr, sizeof(void *), code_ptr + offsets->py_code_object.co_name);
  bpf_probe_read_user_str(&symbol->method_name, sizeof(symbol->method_name), pystr_ptr + offsets->py_string.data);

  // GDB: $frame->f_code->co_firstlineno
  bpf_probe_read_user(&symbol->lineno, sizeof(symbol->lineno), code_ptr + offsets->py_code_object.co_firstlineno);
}
```

We are reading the file name, method name, and line number from the code object. And the module/class name from the frame object for the current frame. Now, we have a full stack, including function names 🚀🚀🚀.

## The Result

 We have the whole stack trace now!

You can see below, not only we can see all the native code and kernel code stack traces, but also we can see the interpreted code stack traces. This is the result of merging the interpreted code stack traces with the native code stack traces. By doing this, we can see the whole picture of a program's execution. And we can see where the time is spent.

Now, we can use this knowledge to focus on the hotspots of our program and optimize them.

> By the way, the following embedded profiles are interactive. Feel free to poke around!

https://pprof.me/e613728/embed/
## Merging the stacks

There is something we have yet to talk about. How do we merge the interpreted code stack traces with the native code stack traces?
### Interpreted stack

The interpreted code execution is not the only thing that is happening in the program. There are also native code and kernel code executions. We have already seen these traces in the beginning of the blog post. Let's remember, how _native stack_ and _kernel stack_ looks like:

https://pprof.me/c06fdcb/embed/

We need to find a way to match the interpreted code stack traces with the native code stack traces. This is a challenging task. We need to find the correct frame in the native code stack trace corresponding to the interpreted code stack trace. One reason behind that, in addition to native stack frames that, is for interpreting the code, we would see native stack frames that the interpreted code potentially called.

For example, in Python, this is the `PyEval_EvalFrameDefault` function. This function is responsible for executing the code and managing the abstract stack. In Ruby, this is the `vm_exec` function. This function is responsible for executing the code and managing the abstract stack.

Naively, we can try to inject the interpreted code stack trace into the native code stack trace, just after the `PyEval_EvalFrameDefault` or `vm_exec` function. However, this might not be 100% correct all the time. So we decided to address this problem in the next releases and for now, we will just inject the interpreted code stack traces after the native stack traces.

## Python and Ruby Support

~~As mentioned in the tl;dr section, we added **beta** support for Python and Ruby languages.~~ This enhancement aims to provide you with a more detailed view of their Python or Ruby programs' performance, allowing them to identify and address potential bottlenecks or performance issues efficiently.

You can profile your Python and Ruby programs using Parca Agent. ~~These features can be enabled using the `--enable-ruby-unwinding` and `--enable-python-unwinding` flags when running the [Parca Agent](https://github.com/parca-dev/parca-agent).~~ As of [v0.28.0 of Parca Agent](https://github.com/parca-dev/parca-agent/releases/tag/v0.28.0), Python and Ruby unwinding is enabled by default 🎉

> Check our [quick start](https://www.parca.dev/docs/quickstart) for more details.

### Supported Interpreters and Versions

Our agent supports [CPython](https://en.wikipedia.org/wiki/CPython) for Python, the default and most widely used implementation. Similarly, for Ruby, we cater to the needs of our users by providing compatibility with [MRI](https://en.wikipedia.org/wiki/Ruby_MRI), also known as Matz's Ruby Interpreter or CRuby, as it is the reference implementation of this language. Our focus remains on accommodating most users by offering functionality that aligns with the most recognized and respected interpreters. We also plan to add support for other implementations in the future if there is a demand for them.

The currently [supported Python (CPython) versions](https://github.com/parca-dev/parca-agent/pull/2019):

**2.7:** 2.7.x

**3.x:** 3.3.7, 3.4.10, 3.5.10, 3.6.15, 3.7.17, 3.8.18, 3.9.18, 3.10.13, 3.11.5

The currently [supported Ruby (MRI) versions](https://github.com/parca-dev/parca-agent/pull/2090):

**2.6:** 2.6.0, 2.6.3

**2.7:** 2.7.1, 2.7.4, 2.7.6

**3.x:** 3.0.0, 3.0.4, 3.1.2, 3.1.3, 3.2.0, 3.2.1

## Give us feedback!

We look forward to your feedback and questions as you explore these new capabilities. For this purpose, we created a dedicated GitHub discussion on the Parca Agent repo. Please check out the following links below 👇

> For [Ruby](https://github.com/parca-dev/parca-agent/discussions/2093) 💎🔴 and for [Python](https://github.com/parca-dev/parca-agent/discussions/2094) 🐍

## What's next?

We can identify and address potential issues or bugs as we test further real-life use cases and more complex applications and programs. We'll also be able to optimize the performance of our tools so you can get the most out of your profiling experience.

We want to explore to add **more runtimes and implementations**! Our tools must be adaptable, so we'll work on compatibility with various runtime environments and language implementations.

We're not stopping at just Python and Ruby - we'll be adding support for even **more programming languages** so you can use our profiling tools for all your favorite projects.

Stay tuned for these updates, and as always, we'd love to hear your thoughts and experiences - so don't hesitate to share them with us!

