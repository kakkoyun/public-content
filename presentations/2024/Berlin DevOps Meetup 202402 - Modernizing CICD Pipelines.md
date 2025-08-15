---
duration: "30"
theme: black
highlightTheme: css/vs2015.css
tags:
  - cicd
  - pipeline
  - devops
---
<!-- slide template="[[tpl-basic-joint-talk]]" -->
# Modernizing CI/CD Pipelines

##### `A Case Study on Building a Robust, Secure, and Efficient System for Cloud-Native Development`

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

`$whoarewe`


<grid drag="30 100" drop="left" justify-content="center">

![](https://avatars.githubusercontent.com/u/536449?v=4) 

Kemal Akkoyun

###### `https://kakkoyun.me`

</grid>

<grid drag="30 100" drop="right">

![](https://aweris.me/images/about.png) 

Ali Akca
###### `https://aweris.me`

</grid>


---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

![[parcadev.png]]

--

<!-- slide template="[[tpl-basic-joint-talk]]" -->

# `eBPF`


![[ebpf diagram.png]]

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->
### Disclaimers

The still ongoing so everything in flux!

--

<!-- slide template="[[tpl-basic-joint-talk]]" -->

1 On-going work

Some of the reasons might overlap and get confusing. Feel free to ask questions

--

<!-- slide template="[[tpl-basic-joint-talk]]" -->

2 We have specific problems!
I hope you do not!

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

3 Probably these are not the only solutions, yet alone not the perfect one! 

Feel free to suggest solutions if you think you know better

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->
## Why?

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

### Reproducibility

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

#### Artifact Reproducibility (Security)

SolarWinds story

Supply chain security
- Byte-by-byte repro
- sigstore (chainguard)
renovate and dependabot

- Superuser previligies
- Too many kernel versions to test on, too many distros, too many everything
    - We need to increase development velocity!

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

#### Build Reproducibility (Developer Experience)

Vendor-locking
Environment (local, CI, test, production)
- it works on my machine!!
Energy efficiency (leads to cost)

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

### Maintainability

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

#### Modern, understandable tooling

No make, bash scripts

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

3

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

## What?

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Reprodubilbe Builds

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

0. Pinning build dependecies
    1. nix (devbox)
    2. renovate and dependabot
2. Reproducible Go/Native binaries
    2. Goreleaser (add link)
3. Reprodubicle containers (timestamps)
    - podman
    - buildx

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

renovate version pinning

```yaml [1,4]
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

- name: Set up Go
  uses: actions/setup-go@93397bea11091df50f3d7e59dc26a7711a8bcfbe # v4.1.0
  with:
    go-version-file: .go-version
    cache: false
```
----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Cross-platform builds

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Go Toolchain
Zig Toolchain
Container-based Cross-platfom builds and images


---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Vendor-locking

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

- The CI/CD locking
    - Cost of Migrate / Upgrade
    - Choose your poison:
        - Dummy wrapper (execute your local scripts) 
            - it works on my machine  
        - Having separate workflows for local and ci/cd
             - push and pray
             
- Environment (local, CI, test, production)
  - it works on my machine!!

- Local CI runs (Dagger)
  - push and pray

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Energy efficiency (leads to cost)

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Maintainability

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Cross-platform testing (future work)

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Container-based solutions
- testcontainers
QEMU 

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

Maintainability/Developer Experience/Fast Feedback cycle

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->


How zenith? Language specific SDK

- Mage (why not make? or why not pure dagger?)
- Dagger

----

<!-- slide template="[[tpl-basic-joint-talk]]" -->

#### What is Dagger?

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

```go 
// Validate runs the build, format, and generate commands and checks if there are any changes in the source code except the out directory.
func (m *CI) Validate() *Container {
	return m.Base.
		WithFocus().
		WithExec([]string{"devbox", "run", "build", "format", "generate"}).
		WithExec([]string{"git", "diff", "--exit-code", ":!out/"})
}
```

::: source
https://github.com/parca-dev/testdata/blob/a92cebddbf420cd95ab3b22b14f15fa36e7c2ef6/ci/main.go#L19-L25
:::

---

<!-- slide template="[[tpl-basic-joint-talk]]" -->

# Thank you!

### Q&A <!-- element class="fragment" -->

---


<!-- slide template="[[tpl-basic-joint-talk]]" -->

<iframe src="https://www.polarsignals.com/jobs/ebpf-engineer" width="1200" height="300" frameborder="0" ></iframe>
::: source
https://www.polarsignals.com/jobs/ebpf-engineer
::: 

--

<!-- slide template="[[tpl-basic-joint-talk]]" -->

<iframe src="https://aweris.me" width="1200" height="320" frameborder="0" ></iframe>

::: source
https://aweris.me
::: 

