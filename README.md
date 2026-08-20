# solana-awesome

A single crate that collects the Solana ecosystem crates and exposes each one
behind a feature flag. Instead of managing a dozen `solana-*` dependencies
(and their version compatibility) in every project, depend on this one crate
and turn on only what you need.

## Usage

```toml
[dependencies]
solana-awesome = { version = "0.1", features = ["pubkey", "keypair", "signer", "rpc-client"] }
```

```rust
use solana_awesome::keypair::Keypair;
use solana_awesome::pubkey::Pubkey;
use solana_awesome::rpc_client::rpc_client::RpcClient;
use solana_awesome::signer::Signer;

let client = RpcClient::new("https://api.devnet.solana.com".to_string());
let payer = Keypair::new();
let balance = client.get_balance(&payer.pubkey())?;
```

Every crate is re-exported as a module named after it, minus the `solana-`
prefix: `solana_awesome::pubkey` is [`solana-pubkey`], `solana_awesome::rpc_client`
is [`solana-rpc-client`], and so on.

## Feature flags

No features are enabled by default.

### Core SDK

| Feature | Crate |
|---|---|
| `pubkey` | `solana-pubkey` |
| `keypair` | `solana-keypair` |
| `signer` | `solana-signer` |
| `signature` | `solana-signature` |
| `instruction` | `solana-instruction` |
| `message` | `solana-message` |
| `transaction` | `solana-transaction` |
| `hash` | `solana-hash` |
| `account` | `solana-account` |
| `commitment-config` | `solana-commitment-config` |
| `native-token` | `solana-native-token` |
| `system-interface` | `solana-system-interface` (with `bincode`, so instruction builders work) |
| `compute-budget-interface` | `solana-compute-budget-interface` |

### Umbrella crates

| Feature | Crate |
|---|---|
| `program` | `solana-program` |

### Clients

| Feature | Crate |
|---|---|
| `client` | `solana-client` |
| `rpc-client` | `solana-rpc-client` |
| `rpc-client-api` | `solana-rpc-client-api` |
| `tpu-client` | `solana-tpu-client` |
| `quic-client` | `solana-quic-client` |
| `udp-client` | `solana-udp-client` |
| `connection-cache` | `solana-connection-cache` |
| `pubsub-client` | `solana-pubsub-client` |
| `transaction-status` | `solana-transaction-status` |
| `account-decoder` | `solana-account-decoder` |

### Groups

| Feature | Enables |
|---|---|
| `core` | all Core SDK features above |
| `clients` | all Client features above |
| `full` | `core` + `clients` + `program` |

## Version pinning notes

- Core crates use major-only requirements (`"3"` / `"4"`) so cargo can unify
  them with the exact minor versions the Agave client crates pin.
- Client crates are pinned to `"4.2"`: letting them float down to 4.1.x pulls
  in `wincode 0.5` alongside the `wincode 0.6` used by the current core
  crates, which fails to compile. Keep the whole client group on the same
  minor version when bumping.

## Adding a new crate

1. `cargo add --optional solana-<name>` (use a major-only version, e.g. `"3"`).
2. Replace the implicit `solana-<name>` feature in `[features]` with a short
   one: `<name> = ["dep:solana-<name>"]`.
3. Add the re-export to `src/lib.rs`:
   `#[cfg(feature = "<name>")] pub use solana_<name> as <name>;`
4. Add it to the `core`/`clients` group if it belongs there, and to the table
   above.
5. `cargo check --features full` and `cargo test --features full`.

[`solana-pubkey`]: https://crates.io/crates/solana-pubkey
[`solana-rpc-client`]: https://crates.io/crates/solana-rpc-client
