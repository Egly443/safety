// Installation check only; this does not verify Codex policy behavior.
#[kani::proof]
fn installation_smoke() {
    let value: u8 = kani::any();
    assert!(value as u16 + 1 <= 256);
}
