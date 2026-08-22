use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use crate::{Block, ChainError};

pub struct ChainDb {
    blocks: Arc<Mutex<HashMap<u64, Block>>>,
    latest_height: Arc<Mutex<u64>>,
    state_entries: Arc<Mutex<HashMap<String, String>>>,
}

impl ChainDb {
    pub fn open<P: AsRef<std::path::Path>>(_path: P) -> Result<Self, ChainError> {
        Ok(Self {
            blocks: Arc::new(Mutex::new(HashMap::new())),
            latest_height: Arc::new(Mutex::new(0)),
            state_entries: Arc::new(Mutex::new(HashMap::new())),
        })
    }

    pub fn put_block(&self, block: &Block) -> Result<(), ChainError> {
        let mut blocks = self.blocks.lock().unwrap();
        let mut height = self.latest_height.lock().unwrap();
        blocks.insert(block.index, block.clone());
        *height = block.index;
        Ok(())
    }

    pub fn get_block_by_height(&self, height: u64) -> Result<Option<Block>, ChainError> {
        let blocks = self.blocks.lock().unwrap();
        Ok(blocks.get(&height).cloned())
    }

    pub fn get_latest_height(&self) -> Result<Option<u64>, ChainError> {
        let height = self.latest_height.lock().unwrap();
        Ok(Some(*height))
    }

    pub fn put_state_entry(&self, key: &str, value: &str) -> Result<(), ChainError> {
        let mut entries = self.state_entries.lock().unwrap();
        entries.insert(key.to_string(), value.to_string());
        Ok(())
    }

    pub fn load_full_chain(&self) -> Result<Vec<Block>, ChainError> {
        let blocks = self.blocks.lock().unwrap();
        let mut chain: Vec<Block> = blocks.values().cloned().collect();
        chain.sort_by_key(|b| b.index);
        Ok(chain)
    }
}
