You are the memory system architect for an eight core chip. The attached cohere12_v1.pdf is the complete specification of its directory coherence protocol, network, cores, workload and design decision. Read the node layout, the directory placement options and every link latency from the figures; they are not printed elsewhere. State the values you read.

Build a cycle accurate simulator of the whole system exactly as the packet specifies, using only the standard library of your chosen language, offline. Record the exact language and runtime version, and give reproduction commands.

Run the baseline configuration (placement P1, Q = 2, B = 2) and report its makespan, p95 load miss latency, total messages and Nacks.

Run all 64 configurations and deliver a CSV with one row per configuration: placement, Q, B, makespan, p95 load miss latency, messages, Nacks. Report the sums over all 64 rows of makespan, messages and Nacks, and the Fastest and Leanest configurations as the packet defines them, with the Fastest's makespan and the Leanest's message count.

Build a separately coded checker that reads a trace of the baseline run written by your simulator and verifies two invariants: at no cycle do two caches hold the same line in state M, and every load returns the value of the most recent store to that line. Report its result for each invariant.

Deliver, as files: the simulator source, the checker source, the sweep CSV, the baseline trace, and an engineering memo. Using your own results, the memo must separate the Fastest configuration's gain over the baseline into its parts by reporting the makespan of placement P2 with Q = 2, B = 2 and of placement P1 with Q = 4, B = 1, and explain what each shows, including why the directory placement matters. It must also state how total Nacks change as Q rises and as B rises, and whether a larger B always shortens the makespan. Base every number on your own executed programs.
