---
duration: 25m
theme: black
highlightTheme: css/vs2015.css
tags:
  - eBPF
  - python
  - profiling
---
<!-- slide template="[[tpl-polar-signals-basic]]" -->

## `Profiling Python with eBPF`


A New Frontier in Performance Analysis

---

<!-- slide template="[[tpl-polar-signals-basic]]" -->

# `$whoami`

--

<!-- slide template="[[tpl-polar-signals-basic]]" -->

![[promio.png]]

--

<!-- slide template="[[tpl-polar-signals-basic]]" -->

![[thanosio.png]]

--

<!-- slide template="[[tpl-polar-signals-basic]]" -->

![[parcadev.png]]

---

<!-- slide template="[[tpl-polar-signals-basic]]" -->

# `Why?`

--

<!-- slide template="[[tpl-polar-signals-basic]]" -->

### Optimization

![[cont_prof_incident.png]]

--

<!-- slide template="[[tpl-polar-signals-basic]]" -->

### Incidents

![[oom.png]]

---
<!-- slide template="[[tpl-polar-signals-basic]]" -->
## `Existing solutions in the Python Ecosystem`

https://docs.python.org/3/library/profile.html
https://github.com/joerick/pyinstrument
**https://github.com/benfred/py-spy**
https://github.com/sumerc/yappi/
https://pyflame.readthedocs.io/en/latest/
https://github.com/plasma-umass/scalene

note: 
- needs instrumentation
- the whole system profiling
	- native
	- kernel
- low-overhead
- DWARF-unwinding

---
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

# `eBPF`


![[ebpf diagram.png]]

--
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

![[perf_events_map.png]]

--
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

### Performance Monitoring Units

`perf_events` began life as a tool for instrumenting the processor's performance monitoring unit (PMU) hardware counters, also called performance monitoring counters (PMCs), or performance instrumentation counters (PICs). 

--
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

## `Prior Art`

[PyPerf code inside the Linux kernel](https://github.com/torvalds/linux/blob/f3a2439f20d918930cc4ae8f76fe1c1afd26958f/tools/testing/selftests/bpf/progs/pyperf.h)

[Python profiler in BCC tools](https://github.com/iovisor/bcc/blob/master/examples/cpp/pyperf/PyPerfBPFProgram.cc)

---
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

# `Parca`

--
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

## `Parca eBPF Agent`


![[agent big picture.png]]

--
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

## `Parca`

![[big picture parca.png|700]]

--

<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

## `Parca Web UI`

![[parca_screenshot.png|700]]

--

<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

![[parca example iciclegraph.png]]

---

<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

## `Stack Unwinding`

![[stack.png|600]]

--

<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

::: title
Stack Unwinding
:::


![[unsymbolized_stack.png]]

---

<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

<iframe src="https://pprof.me/4e5957b/embed/?show_runtime_python=true" width="1200" height="600" frameborder="0" ></iframe>

---

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

## `Unwinding the virtual stack`

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

### Interpreter State


```c
/* interpreter state */

/* PyInterpreterState holds the global state for one of the runtime's
   interpreters.  Typically the initial (main) interpreter is the only one.

   The PyInterpreterState typedef is in Include/pytypedefs.h.
   */
struct _is {

    /* This struct countains the eval_breaker,
     * which is by far the hottest field in this struct
     * and should be placed at the beginning. */
    struct _ceval_state ceval;

    PyInterpreterState *next;

    int64_t id;
    int64_t id_refcount;
    int requires_idref;
    PyThread_type_lock id_mutex;

    /* Has been initialized to a safe state.

       In order to be effective, this must be set to 0 during or right
       after allocation. */
    int _initialized;
    int finalizing;

    uint64_t monitoring_version;
    uint64_t last_restart_version;
    struct pythreads {
        uint64_t next_unique_id;
        /* The linked list of threads, newest first. */
        PyThreadState *head;
        /* The thread currently executing in the __main__ module, if any. */
        PyThreadState *main;
        /* Used in Modules/_threadmodule.c. */
        long count;
        /* Support for runtime thread stack size tuning.
           A value of 0 means using the platform's default stack size
           or the size specified by the THREAD_STACK_SIZE macro. */
        /* Used in Python/thread.c. */
        size_t stacksize;
    } threads;

    /* Reference to the _PyRuntime global variable. This field exists
       to not have to pass runtime in addition to tstate to a function.
       Get runtime from tstate: tstate->interp->runtime. */
    struct pyruntimestate *runtime;

    /* Set by Py_EndInterpreter().

       Use _PyInterpreterState_GetFinalizing()
       and _PyInterpreterState_SetFinalizing()
       to access it, don't access it directly. */
    _Py_atomic_address _finalizing;
    /* The ID of the OS thread in which we are finalizing. */
    unsigned long _finalizing_id;

    struct _gc_runtime_state gc;

    /* The following fields are here to avoid allocation during init.
       The data is exposed through PyInterpreterState pointer fields.
       These fields should not be accessed directly outside of init.

       All other PyInterpreterState pointer fields are populated when
       needed and default to NULL.

       For now there are some exceptions to that rule, which require
       allocation during init.  These will be addressed on a case-by-case
       basis.  Also see _PyRuntimeState regarding the various mutex fields.
       */

    // Dictionary of the sys module
    PyObject *sysdict;

    // Dictionary of the builtins module
    PyObject *builtins;

    struct _import_state imports;

    /* The per-interpreter GIL, which might not be used. */
    struct _gil_runtime_state _gil;

     /* ---------- IMPORTANT ---------------------------
     The fields above this line are declared as early as
     possible to facilitate out-of-process observability
     tools. */

    PyObject *codec_search_path;
    PyObject *codec_search_cache;
    PyObject *codec_error_registry;
    int codecs_initialized;

    PyConfig config;
    unsigned long feature_flags;

    PyObject *dict;  /* Stores per-interpreter state */

    PyObject *sysdict_copy;
    PyObject *builtins_copy;
    // Initialized to _PyEval_EvalFrameDefault().
    _PyFrameEvalFunction eval_frame;

    PyFunction_WatchCallback func_watchers[FUNC_MAX_WATCHERS];
    // One bit is set for each non-NULL entry in func_watchers
    uint8_t active_func_watchers;

    Py_ssize_t co_extra_user_count;
    freefunc co_extra_freefuncs[MAX_CO_EXTRA_USERS];

#ifdef HAVE_FORK
    PyObject *before_forkers;
    PyObject *after_forkers_parent;
    PyObject *after_forkers_child;
#endif

    struct _warnings_runtime_state warnings;
    struct atexit_state atexit;

    struct _obmalloc_state obmalloc;

    PyObject *audit_hooks;
    PyType_WatchCallback type_watchers[TYPE_MAX_WATCHERS];
    PyCode_WatchCallback code_watchers[CODE_MAX_WATCHERS];
    // One bit is set for each non-NULL entry in code_watchers
    uint8_t active_code_watchers;

    struct _py_object_state object_state;
    struct _Py_unicode_state unicode;
    struct _Py_float_state float_state;
    struct _Py_long_state long_state;
    struct _dtoa_state dtoa;
    struct _py_func_state func_state;
    /* Using a cache is very effective since typically only a single slice is
       created and then deleted again. */
    PySliceObject *slice_cache;

    struct _Py_tuple_state tuple;
    struct _Py_list_state list;
    struct _Py_dict_state dict_state;
    struct _Py_async_gen_state async_gen;
    struct _Py_context_state context;
    struct _Py_exc_state exc_state;

    struct ast_state ast;
    struct types_state types;
    struct callable_cache callable_cache;
    _PyOptimizerObject *optimizer;
    uint16_t optimizer_resume_threshold;
    uint16_t optimizer_backedge_threshold;
    uint32_t next_func_version;

    _Py_GlobalMonitors monitors;
    bool f_opcode_trace_set;
    bool sys_profile_initialized;
    bool sys_trace_initialized;
    Py_ssize_t sys_profiling_threads; /* Count of threads with c_profilefunc set */
    Py_ssize_t sys_tracing_threads; /* Count of threads with c_tracefunc set */
    PyObject *monitoring_callables[PY_MONITORING_TOOL_IDS][_PY_MONITORING_EVENTS];
    PyObject *monitoring_tool_names[PY_MONITORING_TOOL_IDS];

    struct _Py_interp_cached_objects cached_objects;
    struct _Py_interp_static_objects static_objects;

   /* the initial PyInterpreterState.threads.head */
    PyThreadState _initial_thread;
};
```

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

### Interpreter State

```c [1-2|4|7]
typedef struct _is PyInterpreterState;

struct _is {
    struct pythreads {
        uint64_t next_unique_id;
        // The linked list of threads, newest first.
        PyThreadState *head;
        // The thread currently executing in 
        // the __main__ module,  if any.
        PyThreadState *main;

    } threads;
};
```


::: source
https://github.com/python/cpython/blob/8c071373f12f325c54591fe990ec026184e48f8f/Include/internal/pycore_interp.h#L42-L209
::: 

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

### Thread State


```c
struct _ts {
    /* See Python/ceval.c for comments explaining most fields */

    PyThreadState *prev;
    PyThreadState *next;
    PyInterpreterState *interp;

    struct {
        /* Has been initialized to a safe state.

           In order to be effective, this must be set to 0 during or right
           after allocation. */
        unsigned int initialized:1;

        /* Has been bound to an OS thread. */
        unsigned int bound:1;
        /* Has been unbound from its OS thread. */
        unsigned int unbound:1;
        /* Has been bound aa current for the GILState API. */
        unsigned int bound_gilstate:1;
        /* Currently in use (maybe holds the GIL). */
        unsigned int active:1;

        /* various stages of finalization */
        unsigned int finalizing:1;
        unsigned int cleared:1;
        unsigned int finalized:1;

        /* padding to align to 4 bytes */
        unsigned int :24;
    } _status;

    int py_recursion_remaining;
    int py_recursion_limit;

    int c_recursion_remaining;
    int recursion_headroom; /* Allow 50 more calls to handle any errors. */

    /* 'tracing' keeps track of the execution depth when tracing/profiling.
       This is to prevent the actual trace/profile code from being recorded in
       the trace/profile. */
    int tracing;
    int what_event; /* The event currently being monitored, if any. */

    /* Pointer to currently executing frame. */
    struct _PyInterpreterFrame *current_frame;

    Py_tracefunc c_profilefunc;
    Py_tracefunc c_tracefunc;
    PyObject *c_profileobj;
    PyObject *c_traceobj;

    /* The exception currently being raised */
    PyObject *current_exception;

    /* Pointer to the top of the exception stack for the exceptions
     * we may be currently handling.  (See _PyErr_StackItem above.)
     * This is never NULL. */
    _PyErr_StackItem *exc_info;

    PyObject *dict;  /* Stores per-thread state */

    int gilstate_counter;

    PyObject *async_exc; /* Asynchronous exception to raise */
    unsigned long thread_id; /* Thread id where this tstate was created */

    /* Native thread id where this tstate was created. This will be 0 except on
     * those platforms that have the notion of native thread id, for which the
     * macro PY_HAVE_THREAD_NATIVE_ID is then defined.
     */
    unsigned long native_thread_id;

    struct _py_trashcan trash;

    /* Called when a thread state is deleted normally, but not when it
     * is destroyed after fork().
     * Pain:  to prevent rare but fatal shutdown errors (issue 18808),
     * Thread.join() must wait for the join'ed thread's tstate to be unlinked
     * from the tstate chain.  That happens at the end of a thread's life,
     * in pystate.c.
     * The obvious way doesn't quite work:  create a lock which the tstate
     * unlinking code releases, and have Thread.join() wait to acquire that
     * lock.  The problem is that we _are_ at the end of the thread's life:
     * if the thread holds the last reference to the lock, decref'ing the
     * lock will delete the lock, and that may trigger arbitrary Python code
     * if there's a weakref, with a callback, to the lock.  But by this time
     * _PyRuntime.gilstate.tstate_current is already NULL, so only the simplest
     * of C code can be allowed to run (in particular it must not be possible to
     * release the GIL).
     * So instead of holding the lock directly, the tstate holds a weakref to
     * the lock:  that's the value of on_delete_data below.  Decref'ing a
     * weakref is harmless.
     * on_delete points to _threadmodule.c's static release_sentinel() function.
     * After the tstate is unlinked, release_sentinel is called with the
     * weakref-to-lock (on_delete_data) argument, and release_sentinel releases
     * the indirectly held lock.
     */
    void (*on_delete)(void *);
    void *on_delete_data;

    int coroutine_origin_tracking_depth;

    PyObject *async_gen_firstiter;
    PyObject *async_gen_finalizer;

    PyObject *context;
    uint64_t context_ver;

    /* Unique thread state id. */
    uint64_t id;

    _PyStackChunk *datastack_chunk;
    PyObject **datastack_top;
    PyObject **datastack_limit;
    /* XXX signal handlers should also be here */

    /* The following fields are here to avoid allocation during init.
       The data is exposed through PyThreadState pointer fields.
       These fields should not be accessed directly outside of init.
       This is indicated by an underscore prefix on the field names.

       All other PyInterpreterState pointer fields are populated when
       needed and default to NULL.
       */
       // Note some fields do not have a leading underscore for backward
       // compatibility.  See https://bugs.python.org/issue45953#msg412046.

    /* The thread's exception stack entry.  (Always the last entry.) */
    _PyErr_StackItem exc_state;

};
```

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

### Thread State

```c [2|12]
// https://github.com/python/cpython/blob/main/Include/pytypedefs.h#L24
typedef struct _ts PyThreadState;

struct _ts {
    PyThreadState *prev;
    PyThreadState *next;
    PyInterpreterState *interp;

    // CODE IS OMITTED for brevity.

    /* Pointer to currently executing frame. */
    struct _PyInterpreterFrame *current_frame;

    int gilstate_counter;

    unsigned long thread_id; /* Thread id where this tstate was created */
    unsigned long native_thread_id;

    // CODE IS OMITTED for brevity.
};
```

::: source
https://github.com/python/cpython/blob/2d4865d775123e8889c7a79fc49b4bf627176c4b/Include/cpython/pystate.h#L64-L195
:::

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

### Interpreter Frame

```c
typedef struct _PyInterpreterFrame {
    PyObject *f_executable; /* Strong reference */
    struct _PyInterpreterFrame *previous;
    PyObject *f_funcobj; /* Strong reference. Only valid if not on C stack */
    PyObject *f_globals; /* Borrowed reference. Only valid if not on C stack */
    PyObject *f_builtins; /* Borrowed reference. Only valid if not on C stack */
    PyObject *f_locals; /* Strong reference, may be NULL. Only valid if not on C stack */
    PyFrameObject *frame_obj; /* Strong reference, may be NULL. Only valid if not on C stack */

	// OMITTED
	
    /* Locals and stack */
    PyObject *localsplus[1];
} _PyInterpreterFrame;
```
::: source
https://github.com/python/cpython/blob/4227bfa8b273207a2b882f7d69c8ac49c3d2b57d/Include/internal/pycore_frame.h#L53-L77
::: 

---

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

## `Where does the code live?`

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->


::: title
Where does code live?
:::

### Find the runtime

```shell
❯ ldd /usr/bin/python3.11
	linux-vdso.so.1 (0x00007ffeca9e2000)
	libpython3.11.so.1.0 => /usr/lib/libpython3.11.so.1.0 (0x00007fe6eaa00000)
	libc.so.6 => /usr/lib/libc.so.6 (0x00007fe6ea81e000)
	libm.so.6 => /usr/lib/libm.so.6 (0x00007fe6eb06f000)
	/lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x00007fe6eb18e000)
```

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Where does code live?
:::
### Find the runtime structs

```shell
❯ nm /usr/lib/libpython3.11.so.1.0 | grep PyRuntime
0000000000557d20 D _PyRuntime
0000000000297290 T _PyRuntime_Finalize
0000000000297220 T _PyRuntime_Initialize
000000000029a7a0 T _PyRuntimeState_Fini
000000000029a600 T _PyRuntimeState_Init
000000000029a840 t _PyRuntimeState_ReInitThreads
```


--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->


::: title
Where does code live?
:::
### Address space layout randomization

###### `https://en.wikipedia.org/wiki/Address_space_layout_randomization`

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Where does code live?
:::
### Loaded program

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

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->


::: title
Where does code live?
::: 
### Mappings

```shell
❯ cat /proc/18535/maps | grep libpython3.11.so.1.0
7f0882a00000-7f0882aee000 r--p 00000000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
7f0882aee000-7f0882d3d000 r-xp 000ee000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
7f0882d3d000-7f0882e2a000 r--p 0033d000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
7f0882e2a000-7f0882e59000 r--p 0042a000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
7f0882e59000-7f0882f89000 rw-p 00459000 fe:00 4212985                    /usr/lib/libpython3.11.so.1.0
```


---

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

## `Reading the data from the memory`

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Reading the data from the memory
:::
### GDB

[GDB](https://www.gnu.org/software/gdb/) is a debugger that allows us to inspect any program while it is running.

```text
❯ gdb -p $(pidof python)
GNU gdb (GDB) 13.2
Copyright (C) 2023 Free Software Foundation, Inc.
For help, type "help".
Type "apropos word" to search for commands related to "word".
Attaching to process 273506
```

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Reading the data from the memory
::: 

### Field Offsets

```text
> macro define offsetof(t, f) &((t *) 0)->f
> p/d offsetof(PyRuntimeState, interp)
$1 = 48 # This is the offset of the `interp` field in the `PyRuntimeState` struct
```

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Reading the data from the memory
:::
### Generating type information ahead of time

## [parca-dev/runtime-data](https://github.com/parca-dev/runtime-data) 

#### [Rust Bindgen](https://github.com/rust-lang/rust-bindgen)<!-- element class="fragment" -->

#### DWARF-based reader <!-- element class="fragment" -->

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Reading the data from the memory
:::

### Offsets

```c
typedef struct {
  u32 major_version;
  u32 minor_version;
  u32 patch_version;

  PyCFrame py_cframe;
  PyCodeObject py_code_object;
  PyFrameObject py_frame_object;
  PyInterpreterState py_interpreter_state;
  PyObject py_object;
  PyRuntimeState py_runtime_state;
  PyString py_string;
  PyThreadState py_thread_state;
  PyTupleObject py_tuple_object;
  PyTypeObject py_type_object;
} PythonVersionOffsets;
```

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Reading the data from the memory
:::

# >=3.13

```c
typedef struct pyruntimestate {
    /* This field must be first to facilitate locating it 
     * by out of process
     * debuggers. Out of process debuggers will
     * use the offsets contained in this
     * field to be able to locate other fields 
     * in several interpreter structures
     * in a way that doesn't require them to know 
     * the exact layout of those structures.
     *
     * IMPORTANT:
     * This struct is **NOT** backwards compatible between 
     * minor version of the interpreter and the members, 
     * the order of members and size can change between
     * minor versions. 
     * This struct is only guaranteed to be stable between
     * patch versions for a given minor version of 
     * the interpreter.
     */
    _Py_DebugOffsets debug_offsets;
}
```
<!-- element style="font-size: 16px;" class="small-indent" -->

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Reading the data from the memory
:::

# >=3.13

```c
typedef struct _Py_DebugOffsets {
    char cookie[8];
    uint64_t version;
    // Runtime state offset;
    struct _runtime_state {
        off_t finalizing;
        off_t interpreters_head;
    } runtime_state;

    // Interpreter state offset;
    struct _interpreter_state {
        off_t next;
        off_t threads_head;
        off_t gc;
        off_t imports_modules;
        off_t sysdict;
        off_t builtins;
        off_t ceval_gil;
        off_t gil_runtime_state_locked;
        off_t gil_runtime_state_holder;
    } interpreter_state;

    // Thread state offset;
    struct _thread_state{
        off_t prev;
        off_t next;
        off_t interp;
        off_t current_frame;
        off_t thread_id;
        off_t native_thread_id;
    } thread_state;

    // InterpreterFrame offset;
    struct _interpreter_frame {
        off_t previous;
        off_t executable;
        off_t instr_ptr;
        off_t localsplus;
        off_t owner;
    } interpreter_frame;
    // CFrame offset;
    struct _cframe {
        off_t current_frame;
        off_t previous;
    } cframe;

    // Code object offset;
    struct _code_object {
        off_t filename;
        off_t name;
        off_t linetable;
        off_t firstlineno;
        off_t argcount;
        off_t localsplusnames;
        off_t localspluskinds;
        off_t co_code_adaptive;
    } code_object;

    // PyObject offset;
    struct _pyobject {
        off_t ob_type;
    } pyobject;

    // PyTypeObject object offset;
    struct _type_object {
        off_t tp_name;
    } type_object;

    // PyTuple object offset;
    struct _tuple_object {
        off_t ob_item;
    } tuple_object;
} _Py_DebugOffsets;
```


---

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

## `Unwinding the stack`

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Unwinding the stack
::: 
### Initial State

```c [1-2]
InterpreterInfo *interpreter_info = 
	bpf_map_lookup_elem(&pid_to_interpreter_info, &pid);
if (!interpreter_info) {
    LOG("[error] interpreter_info is NULL, not a Python process or unknown Python version");
    return 0;
}
```

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Unwinding the stack
::: 
### Initial State

```go [9-10]
func InterpreterInfo(proc procfs.Proc) (*runtime.Interpreter, error) {
	// ...
	return &runtime.Interpreter{
		Runtime: runtime.Runtime{
			Name:    "Python",
			Version: interpreter.version.String(),
		},
		Type:               runtime.InterpreterPython,
		MainThreadAddress:  threadStateAddress,
		InterpreterAddress: interpreterAddress,
	}, nil
}
```

--

<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Unwinding the stack
::: 

### Read the Offsets

```c
// GET_OFFSETS();

PythonVersionOffsets *offsets = bpf_map_lookup_elem(&version_specific_offsets, &state->interpreter_info.py_version_offset_index);
if (offsets == NULL) {             
	return 0;
}
```


--
<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Unwinding the stack
::: 

### Find the virtual Frame Pointer

```c [1]
LOG("offsets->py_thread_state.cframe %d", 
	offsets->py_thread_state.cframe);
void *cframe;
bpf_probe_read_user(&cframe, sizeof(cframe), 
					(void *)(state->thread_state + offsets->py_thread_state.cframe));
if (cframe == 0) {
  LOG("[error] cframe was NULL");
  goto submit_without_unwinding;
}

LOG("offsets->py_cframe.current_frame %d", 
	offsets->py_cframe.current_frame);
bpf_probe_read_user(&state->frame_ptr, sizeof(state->frame_ptr), 
					(void *)(cframe + offsets->py_cframe.current_frame));
```

--
<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Unwinding the stack
:::

### Walk the Stack

```c [1|14|21|35|42|46|51]
int walk_python_stack(struct bpf_perf_event_data *ctx) {
  u64 zero = 0;
  GET_STATE();
  GET_OFFSETS();

  LOG("=====================================================\n");
  LOG("[start] walk_python_stack");
  state->stack_walker_prog_call_count++;
  Sample *sample = &state->sample;

  int frame_count = 0;
#pragma unroll
  for (int i = 0; i < PYTHON_STACK_FRAMES_PER_PROG; i++) {
    void *cur_frame = state->frame_ptr;
    if (!cur_frame) {
      break;
    }

    // Read the code pointer. PyFrameObject.f_code
    void *cur_code_ptr;
    bpf_probe_read_user(&cur_code_ptr, sizeof(cur_code_ptr), state->frame_ptr + offsets->py_frame_object.f_code);
    if (!cur_code_ptr) {
      LOG("[error] bpf_probe_read_user failed");
      break;
    }

    LOG("## frame %d", frame_count);
    LOG("\tcur_frame_ptr 0x%llx", cur_frame);
    LOG("\tcur_code_ptr 0x%llx", cur_code_ptr);

    symbol_t sym = (symbol_t){0};
    reset_symbol(&sym);

    // Read symbol information from the code object if possible.
    u64 lineno = read_symbol(offsets, cur_frame, cur_code_ptr, &sym);

    LOG("\tsym.path %s", sym.path);
    LOG("\tsym.class_name %s", sym.class_name);
    LOG("\tsym.method_name %s", sym.method_name);
    LOG("\tsym.lineno %d", lineno);

    u64 symbol_id = get_symbol_id(&sym);
    u64 cur_len = sample->stack.len;
    if (cur_len >= 0 && cur_len < MAX_STACK_DEPTH) {
      LOG("\tstack->frames[%llu] = %llu", cur_len, symbol_id);
      sample->stack.addresses[cur_len] = (lineno << 32) | symbol_id;
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


--
<!-- slide template="[[tpl-polar-signals-basic]]"  -->

::: title
Unwinding the stack
:::

### Reading the symbols

```c [2|5|19|23|27]
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

---
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

##### Voilà 🎉

<iframe src="https://pprof.me/e613728/embed/?show_runtime_python=true" width="1200" height="500" frameborder="0" ></iframe>

---
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->
### Supported Interpreters and Versions

Our agent supports [CPython](https://en.wikipedia.org/wiki/CPython) for Python, the default and most widely used implementation. 

The currently [supported Python (CPython) versions](https://github.com/parca-dev/parca-agent/pull/2019):


+ **2.7:** 2.7.x
+ **3.x:** 3.3.x, 3.4.x, 3.5.x, 3.6.x, 3.7.x, 3.8.x, 3.9.x, 3.10.x, 3.11.x


---
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->
## Give us feedback!

https://github.com/parca-dev/parca-agent/discussions/2094

![[python_discussion_exported_qrcode_image_600.png|300]] <!-- element class="fragment" -->

---
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

<iframe src="https://www.polarsignals.com/blog/posts/2023/10/04/profiling-python-and-ruby-with-ebpf" width="1200" height="500" frameborder="0" ></iframe>

::: source
https://www.polarsignals.com/blog/posts/2023/10/04/profiling-python-and-ruby-with-ebpf
:::

---
<!-- slide template="[[tpl-polar-signals-basic-white]]"  -->

<iframe src="https://www.polarsignals.com/blog/posts/2022/11/29/dwarf-based-stack-walking-using-ebpf" width="1200" height="500" frameborder="0" ></iframe>

::: source
https://www.polarsignals.com/blog/posts/2022/11/29/dwarf-based-stack-walking-using-ebpf
:::

---

# Thank you!

### Q&A <!-- element class="fragment" -->

---

<!-- slide template="[[tpl-polar-signals-basic]]" -->
## $ whoami

# :sweat_smile:

<i class="fab fa-twitter"></i> kkakkoyun

<i class="fab fa-github"></i> <i class="fab fa-linkedin"></i> kakkoyun