You are the memory system architect for an eight core chip. The attached cohere12_v2.pdf is the complete specification of its directory coherence protocol, network, cores, workload, configuration space and objective. Read the node layout, every link latency and the baseline line map from the figures; they are not printed elsewhere. State the values you read, including the baseline line map number.

Build a cycle accurate simulator of the whole system exactly as the packet specifies, using only the standard library of your chosen language, offline. Record the exact language and runtime version, and give reproduction commands.

Run the baseline (D0 on N0, D1 on N7, Q = 2, B = 2, line map of Figure 5) and report its makespan, p95 load miss latency, messages and Nacks. Also report the makespan of three variants of the baseline: line map 43690 instead of Figure 5's; D0 on N1 and D1 on N6 instead; and D0 on N1, D1 on N6 with Q = 4 and B = 1.

Find the optimal configuration as the packet defines it. Report its directory nodes, line map number, Q, B, makespan and messages, and for each value of Q the best configuration with that Q and its makespan. State how many configurations you evaluated and whether your search covered the whole space; call a configuration optimal only if it did.

Build a separately coded checker that reads a trace of the baseline run written by your simulator and verifies two invariants: at no cycle do two caches hold the same line in state M, and every load returns the value of the most recent store to that line. Report its result for each invariant.

Deliver, as files: the simulator source, the checker source, the baseline trace, a CSV of the 20 best configurations you found (directory nodes, line map number, Q, B, makespan, messages), and an engineering memo explaining your search method and why your best configuration beats the baseline. Base every number on your own executed programs.
