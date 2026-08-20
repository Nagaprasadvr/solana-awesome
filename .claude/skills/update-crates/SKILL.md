---
name: update-crates
description: Check crates.io for new solana-* crates and version bumps, curate and apply them to solana-awesome, validate, and prep (but not perform) a release.
---

# Update solana-awesome from crates.io

You are maintaining an umbrella crate that re-exports Solana ecosystem crates
behind feature flags. Keep it current in two ways: bump version requirements
of existing dependencies, and add newly published crates that belong here.

## 1. Gather the report

Run `python3 scripts/check_crates.py` from the repo root (read-only; takes a
few minutes because it rate-limits crates.io requests). It reports available
version bumps and new trusted-owner candidates, already filtered against
`scripts/crates-denylist.txt` and staleness/placeholder heuristics.

## 2. Apply version bumps

Requirement philosophy in `Cargo.toml`:
- Core SDK crates use **major-only** requirements (`"4"`) so cargo can unify
  them with whatever the client crates pin.
- Client crates (the `solana-client`/`solana-rpc-client` family) use
  **major.minor** (`"4.2"`) and must move together to the same minor.

For each reported bump, widen or advance the requirement accordingly. A new
major version of a dependency may change its API — check the smoke tests
still compile and adjust imports if the crate moved types around.

## 3. Curate new candidates

Include a candidate only if downstream app or program developers would use it
as a library: SDK primitives and types, `*-interface` crates, clients,
crypto/hashing utilities, dev-test frameworks like `solana-program-test`.

Reject validator/node internals, on-chain program runtime implementations
(prefer their `*-interface` crate), CLIs/binaries, internal-use-only crates,
wasm/JS bindings, and deprecated or 0.0.x placeholder crates. When in doubt,
check the crate's docs.rs page and reverse dependencies.

**Every rejection must be recorded**: append the crate name to
`scripts/crates-denylist.txt` under the fitting section with a `# reason`
comment when the name alone isn't self-explanatory. This is what keeps the
next run's report short.

## 4. Wire in each accepted crate

For a crate `solana-foo-bar`:
1. `Cargo.toml` dependencies: `solana-foo-bar = { version = "N", optional = true }`
   in the matching section (major-only unless it must lockstep with clients).
   Keep the section sorted alphabetically.
2. `Cargo.toml` features: `foo-bar = ["dep:solana-foo-bar"]`, and add
   `foo-bar` to the right group feature (`core`, `clients`, or a new group if
   a genuinely new category emerges — remember `full` must cover all groups).
3. `src/lib.rs`: `#[cfg(feature = "foo-bar")] pub use solana_foo_bar as foo_bar;`
   under the matching section comment.
4. `README.md`: add a row to the matching feature table.
5. `tests/smoke.rs`: add a feature-gated test when there's an obvious cheap
   assertion (construct a type, check a constant or program ID). Skip if a
   meaningful test would need a network or validator.

## 5. Validate

```
cargo update
cargo test --features full
cargo doc --features full --no-deps
```

Also spot-check that a single lone feature compiles, e.g.
`cargo check --no-default-features --features foo-bar` for one new crate.

## 6. Version and summarize

Bump `package.version` in `Cargo.toml`: **patch** if only dependency
requirements changed, **minor** if features were added. Summarize what was
bumped, added, and denylisted.

**Do not publish or push.** Releases are manual — point the user at the
Release section in `README.md` when the tree is ready.
