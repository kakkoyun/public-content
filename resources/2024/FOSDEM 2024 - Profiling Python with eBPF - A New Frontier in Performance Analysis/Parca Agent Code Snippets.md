```c
InterpreterInfo *interpreter_info = bpf_map_lookup_elem(&pid_to_interpreter_info, &pid);
  if (!interpreter_info) {
    LOG("[error] interpreter_info is NULL, not a Python process or unknown Python version");
    return 0;
  }
```

```c
PythonVersionOffsets *offsets = bpf_map_lookup_elem(&version_specific_offsets, &state->interpreter_info.py_version_offset_index);
  if (offsets == NULL) {                                                    
    return 0;                                                               
  }
```

```c
LOG("offsets->py_thread_state.cframe %d", offsets->py_thread_state.cframe);
    void *cframe;
    bpf_probe_read_user(&cframe, sizeof(cframe), (void *)(state->thread_state + offsets->py_thread_state.cframe));
    if (cframe == 0) {
      LOG("[error] cframe was NULL");
      goto submit_without_unwinding;
    }
    LOG("cframe 0x%llx", cframe);

    LOG("offsets->py_cframe.current_frame %d", offsets->py_cframe.current_frame);
    bpf_probe_read_user(&state->frame_ptr, sizeof(state->frame_ptr), (void *)(cframe + offsets->py_cframe.current_frame));
```

```c
SEC("perf_event")
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

```go
func (i interpreter) tstateCurrentOffset() (uint64, error) {
	switch i.arch {
	case "amd64":
		return i.tstateCurrentOffsetAmd64()
	case "arm64":
		return i.tstateCurrentOffsetArm64()
	default:
		return 0, fmt.Errorf("unsupported architecture: %s", goruntime.GOARCH)
	}
}

// https://github.com/benfred/py-spy/blob/8a0d06d1b4ca986a061642b87e578112c2f5ab7b/src/python_bindings/mod.rs#L171
func (i interpreter) tstateCurrentOffsetArm64() (uint64, error) {
	switch {
	case const3703.Check(i.version):
		return 1408, nil
	case const37.Check(i.version):
		return 1496, nil
	case const380.Check(i.version):
		return 1384, nil
	case const39_10.Check(i.version):
		return 584, nil
	case const311.Check(i.version):
		return 592, nil
	default:
		return 0, fmt.Errorf("unsupported version: %s", i.version.String())
	}
}

// https://github.com/benfred/py-spy/blob/8a0d06d1b4ca986a061642b87e578112c2f5ab7b/src/python_bindings/mod.rs#L201
func (i interpreter) tstateCurrentOffsetAmd64() (uint64, error) {
	switch {
	case const3703.Check(i.version):
		return 1392, nil
	case const37.Check(i.version):
		return 1480, nil
	case const380.Check(i.version):
		return 1368, nil
	case const3810.Check(i.version):
		return 1368, nil
	case const39_10.Check(i.version):
		return 568, nil
	case const311.Check(i.version):
		return 576, nil
	default:
		return 0, fmt.Errorf("unsupported version: %s", i.version.String())
	}
}
```

```go
func InterpreterInfo(proc procfs.Proc) (*runtime.Interpreter, error) {
	interpreter, err := newInterpreter(proc)
	if err != nil {
		return nil, fmt.Errorf("new interpreter: %w", err)
	}
	defer interpreter.Close()

	threadStateAddress, err := interpreter.threadStateAddress()
	if err != nil {
		return nil, fmt.Errorf("python version: %s, thread state address: %w", interpreter.version.String(), err)
	}
	if threadStateAddress == 0 {
		return nil, fmt.Errorf("invalid address, python version: %s, thread state address: 0x%016x", interpreter.version.String(), threadStateAddress)
	}

	interpreterAddress, err := interpreter.interpreterAddress()
	if err != nil {
		return nil, fmt.Errorf("python version: %s, interpreter address: %w", interpreter.version.String(), err)
	}
	if interpreterAddress == 0 {
		return nil, fmt.Errorf("invalid address, python version: %s, interpreter address: 0x%016x", interpreter.version.String(), interpreterAddress)
	}

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

```c
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 1); // Set in the user-space.
    __type(key, symbol_t);
    __type(value, u32);
} symbol_table SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, u32);
    __type(value, u32);
} symbol_index_storage SEC(".maps");

const volatile int num_cpus = 200; // Hard-limit of 200 CPUs.

static inline __attribute__((__always_inline__))
u32 get_symbol_id(symbol_t *sym) {
	int *found_id = bpf_map_lookup_elem(&symbol_table, sym);
	if (found_id) {
		return *found_id;
	}

	u32 zero = 0;
	u32 *sym_idx = bpf_map_lookup_elem(&symbol_index_storage, &zero);
	if (sym_idx == NULL) {
		// Appease the verifier, this will never fail.
		return 0;
	}

	// u32 idx = __sync_fetch_and_add(sym_idx, 1);
	// The previous __sync_fetch_and_add does not seem to work in 5.4 and 5.10
	//  > libbpf: prog 'walk_ruby_stack': -- BEGIN PROG LOAD LOG --\nBPF_STX uses reserved fields
	//
	// Checking for the version does not work as these branches are not pruned
	// in older kernels, so we shard the id generation per CPU.
	u32 idx = *sym_idx * num_cpus + bpf_get_smp_processor_id();
	*sym_idx += 1;

	int err;
	err = bpf_map_update_elem(&symbol_table, sym, &idx, BPF_ANY);
	if (err) {
		return 0;
	}
	return idx;
}
```

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