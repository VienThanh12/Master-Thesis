// Rust counterpart to cpp/iterator_invalidation.cpp (iterator invalidation).
// Iterating `&drbs` holds a shared borrow for the whole loop; pushing into it needs
// a mutable borrow at the same time, which the borrow checker rejects (E0502).
struct DrbEntry {
    drb_id: i32,
}

fn main() {
    let mut drbs: Vec<DrbEntry> = (0..8).map(|i| DrbEntry { drb_id: i }).collect();

    for d in &drbs {
        // shared borrow of `drbs` held across the loop body
        if d.drb_id == 3 {
            drbs.push(DrbEntry { drb_id: 99 }); // mutable borrow while borrowed -> rejected
        }
        println!("drb_id={}", d.drb_id);
    }
}
