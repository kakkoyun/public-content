https://github.com/python/cpython/blob/8c071373f12f325c54591fe990ec026184e48f8f/Include/internal/pycore_interp.h#L42-L209

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

---

https://github.com/python/cpython/blob/2d4865d775123e8889c7a79fc49b4bf627176c4b/Include/cpython/pystate.h#L64-L195

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

---

https://github.com/python/cpython/blob/4227bfa8b273207a2b882f7d69c8ac49c3d2b57d/Include/internal/pycore_frame.h#L53-L77

```c
typedef struct _PyInterpreterFrame {
    PyObject *f_executable; /* Strong reference */
    struct _PyInterpreterFrame *previous;
    PyObject *f_funcobj; /* Strong reference. Only valid if not on C stack */
    PyObject *f_globals; /* Borrowed reference. Only valid if not on C stack */
    PyObject *f_builtins; /* Borrowed reference. Only valid if not on C stack */
    PyObject *f_locals; /* Strong reference, may be NULL. Only valid if not on C stack */
    PyFrameObject *frame_obj; /* Strong reference, may be NULL. Only valid if not on C stack */
    // NOTE: This is not necessarily the last instruction started in the given
    // frame. Rather, it is the code unit *prior to* the *next* instruction. For
    // example, it may be an inline CACHE entry, an instruction we just jumped
    // over, or (in the case of a newly-created frame) a totally invalid value:
    _Py_CODEUNIT *prev_instr;
    int stacktop;  /* Offset of TOS from localsplus  */
    /* The return_offset determines where a `RETURN` should go in the caller,
     * relative to `prev_instr`.
     * It is only meaningful to the callee,
     * so it needs to be set in any CALL (to a Python function)
     * or SEND (to a coroutine or generator).
     * If there is no callee, then it is meaningless. */
    uint16_t return_offset;
    char owner;
    /* Locals and stack */
    PyObject *localsplus[1];
} _PyInterpreterFrame;
```