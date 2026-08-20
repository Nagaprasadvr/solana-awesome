//! Smoke tests exercising the feature-gated re-exports.
//! Run with: cargo test --features full

#[cfg(feature = "pubkey")]
#[test]
fn pubkey_reexport() {
    use solana_awesome::pubkey::Pubkey;
    use std::str::FromStr;

    let key = Pubkey::from_str("11111111111111111111111111111111").unwrap();
    assert_eq!(key, Pubkey::default());
}

#[cfg(all(feature = "keypair", feature = "signer", feature = "signature"))]
#[test]
fn keypair_signs() {
    use solana_awesome::keypair::Keypair;
    use solana_awesome::signer::Signer;

    let keypair = Keypair::new();
    let signature = keypair.sign_message(b"hello");
    assert!(signature.verify(keypair.pubkey().as_ref(), b"hello"));
}

#[cfg(all(
    feature = "system-interface",
    feature = "pubkey",
    feature = "instruction"
))]
#[test]
fn system_transfer_instruction() {
    use solana_awesome::pubkey::Pubkey;
    use solana_awesome::system_interface::instruction::transfer;

    let from = Pubkey::new_unique();
    let to = Pubkey::new_unique();
    let ix = transfer(&from, &to, 1);
    assert_eq!(ix.program_id, solana_awesome::system_interface::program::ID);
}

#[cfg(all(feature = "rpc-client", feature = "commitment-config"))]
#[test]
fn rpc_client_constructs() {
    use solana_awesome::commitment_config::CommitmentConfig;
    use solana_awesome::rpc_client::rpc_client::RpcClient;

    let client = RpcClient::new_with_commitment(
        "http://127.0.0.1:8899".to_string(),
        CommitmentConfig::confirmed(),
    );
    assert_eq!(client.commitment(), CommitmentConfig::confirmed());
}

#[cfg(feature = "native-token")]
#[test]
fn native_token_constants() {
    use solana_awesome::native_token::LAMPORTS_PER_SOL;
    assert_eq!(LAMPORTS_PER_SOL, 1_000_000_000);
}
