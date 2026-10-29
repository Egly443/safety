# Controlled Cloud retry

Use a published Linux x86-64 Cloud environment with nominal memory of at least
16 GiB and at least 20 GiB free disk before setup. Confirm its actual resource
limits. Do not purchase or provision external resources. No Cloud task has been
launched from the laptop: no execution environment is attached, and the local
CLI environment picker exposed no selectable environment.

The first actual-code attempt compiled successfully but hit the laptop's 4 GiB
sampled RSS guard after 777.761 seconds, at 4.019 GiB observed RSS. A shorter-path
fixture with unwind 16 hit a five-minute wall limit at 2.364 GiB observed RSS.
Both are inconclusive. Neither produced a proof or a safety counterexample.
The second attempt changed both path literals and the unwind bound, so their
individual effects have not been isolated. Cold/warm compilation also differs.

The Cloud retry uses exactly the current short fixture and production source,
with all unwinding and safety assertions retained. It changes operational
budgets only: 8 GiB sampled aggregate RSS and 20 minutes including compilation.
There are no stubs and no rewritten policy or path implementations.

From the extracted payload root:

```
bash scripts/cloud-kani-bootstrap.sh
bash scripts/kani-feasibility.sh --seconds 1200 --rss-gib 8
```

Setup requires standard compiler tools, Rust, and OpenSSL development files.
If a tool or network destination is unavailable, report the exact setup issue
and resolve it through the published environment's setup/network workflow.
Preserve inherited proxy settings and TLS verification. Never include credentials
or unrelated environment values in output. No API key is needed by this proof job.

Do not build the full CLI, run the VM, alter the fixture, disable checks, or
implement additional claims in this retry. Do not commit, push, or open a PR.
Do not label the smoke case as the intended symbolic bounded theorem.

Return `evidence/kani-feasibility.log`, `kani-feasibility-resources.json`,
`kani-source-manifest.json`, worktree diff, and exact Kani/Rust/CBMC versions.
A successful exit alone is insufficient: inspect the number of harnesses,
assertions and unwinding checks. Resource stops remain inconclusive. If the
smoke case succeeds, the next stage is a must-fail reachability control before
constructing the bounded symbolic domain. More resources are not guaranteed to
solve the symbolic-execution cost.

Official Cloud setup and VM specifications:
https://learn.chatgpt.com/docs/environments/cloud-environments#vm-specifications
