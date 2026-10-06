You are the memory system architect for an eight core chip. The attached cohere12_v1.pdf is the complete specification of its directory coherence protocol, network, cores, workload and the design decision. Read the node layout, directory placement options and link latencies from the figures; they are not printed elsewhere. State the values you read.

Build a cycle accurate simulator of the whole system exactly as the packet specifies, using only the standard library of your chosen language, offline. Record the exact language and runtime version, and give reproduction commands.

Run the baseline configuration P1, Q = 2, B = 2 and report its makespan, each core's finish cycle, the p95 load miss latency, and the number of messages created of each type.

Run all 64 configurations of the sweep and deliver a CSV with one row per configuration: placement, Q, B, makespan, p95 load miss latency, messages, Nacks. Report the Fastest and the Leanest configurations as the packet defines them, and the sums over all 64 rows of makespan, messages and Nacks.

Build a separately coded checker that reads a trace of the baseline run written by your simulator and verifies two invariants: at no cycle do two caches hold the same line in M, and every load returns the value of the most recent store to that line. Report its result.

Deliver, as files: the simulator source, the checker source, the sweep CSV, the baseline trace, and a memo that explains, using your own results, why the Fastest configuration beats the baseline and how Q and B trade Nacks against makespan. Base every number on your own executed programs.
