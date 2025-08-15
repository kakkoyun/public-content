The -toolexec flag hides a super-power in the Go toolchain: it lets you turn every go build into a programmable pipeline. In this session we’ll reveal how a simple wrapper command can inject custom analysis, code generation, and instrumentation—without changing a line of application code.

You’ll see how platform and tooling teams use -toolexec to weave organisation-wide practices directly into the build, from enforcing error-handling standards to automatically adding observability hooks. We’ll map the journey from a “hello-world” wrapper to full Aspect-Oriented compile-time transformations, and discuss the trade-offs that come with this new power.

Along the way we’ll spotlight real projects—such as Datadog’s Orchestrion—and community efforts in compile-time instrumentation, showing what’s already possible and where the ecosystem is heading. Finally, we’ll share practical tips for keeping builds fast and reliable when you venture beyond the default toolchain path.

If you’re curious about bending the Go compiler to your will—and doing so responsibly—this talk will equip you with the concepts, examples, and inspiration to start experimenting the moment you’re back at your editor.
