use candle_core::{DType, Device, Tensor};
use candle_nn::VarBuilder;
use candle_transformers::models::bert::{BertModel, Config};
use std::path::Path;
use thiserror::Error;
use tokenizers::Tokenizer;

#[derive(Error, Debug)]
pub enum InferenceError {
    #[error("CUDA initialization failed: {0}")]
    CudaInitError(String),
    #[error("Failed to load tokenizer from '{0}': {1}")]
    TokenizerLoadError(String, String),
    #[error("Tokenizer encoding failure: {0}")]
    TokenizationError(String),
    #[error("Model configuration read error from '{0}': {1}")]
    ConfigError(String, String),
    #[error("Weights VarBuilder error from '{0}': {1}")]
    WeightsLoadError(String, String),
    #[error("Model forward execution failed: {0}")]
    ForwardError(String),
    #[error("Tensor transformation failure: {0}")]
    TensorError(String),
}

/// Native embedded neural inference engine running directly on CUDA
pub struct EmbeddedNeuralEngine {
    device: Device,
    tokenizer: Tokenizer,
    model: BertModel,
}

impl EmbeddedNeuralEngine {
    /// Loads BERT/Nomic weights directly from disk into GPU VRAM using memory-mapped safetensors
    pub fn load_from_disk<P: AsRef<Path>>(
        config_path: P,
        tokenizer_path: P,
        weights_path: P,
        gpu_ordinal: usize,
    ) -> Result<Self, InferenceError> {
        let config_ref = config_path.as_ref();
        let tokenizer_ref = tokenizer_path.as_ref();
        let weights_ref = weights_path.as_ref();

        // 1. Initialize CUDA or CPU device
        let device = Device::new_cuda(gpu_ordinal).unwrap_or(Device::Cpu);

        tracing::info!("[*] Initialized Inference Device on RTX 5090 / CPU");

        // 2. Load and parse model Config
        let config_str = std::fs::read_to_string(config_ref).map_err(|e| {
            InferenceError::ConfigError(config_ref.display().to_string(), e.to_string())
        })?;
        let config: Config = serde_json::from_str(&config_str).map_err(|e| {
            InferenceError::ConfigError(config_ref.display().to_string(), e.to_string())
        })?;

        // 3. Load Tokenizer
        let tokenizer = Tokenizer::from_file(tokenizer_ref).map_err(|e| {
            InferenceError::TokenizerLoadError(tokenizer_ref.display().to_string(), e.to_string())
        })?;

        // 4. Memory-map safetensors directly into device memory
        let vb = unsafe {
            VarBuilder::from_mmaped_safetensors(&[weights_ref], DType::F32, &device).map_err(|e| {
                InferenceError::WeightsLoadError(weights_ref.display().to_string(), e.to_string())
            })?
        };

        // 5. Instantiate the model on device
        let model = BertModel::load(vb, &config).map_err(|e| {
            InferenceError::WeightsLoadError(weights_ref.display().to_string(), e.to_string())
        })?;

        tracing::info!(
            "[+] Model & Tokenizer successfully resident in VRAM from: {}",
            weights_ref.display()
        );

        Ok(Self {
            device,
            tokenizer,
            model,
        })
    }

    /// High-throughput zero-copy embedding computation with L2 normalization
    pub fn embed_batch(&self, texts: &[&str]) -> Result<Vec<Vec<f32>>, InferenceError> {
        if texts.is_empty() {
            return Ok(vec![]);
        }

        // 1. Encode text inputs with batch padding
        let encodings = self
            .tokenizer
            .encode_batch(texts.to_vec(), true)
            .map_err(|e| InferenceError::TokenizationError(e.to_string()))?;

        let batch_size = encodings.len();
        let max_len = encodings.iter().map(|e| e.get_ids().len()).max().unwrap_or(0);

        let mut token_ids_flat = Vec::with_capacity(batch_size * max_len);
        let mut attention_mask_flat = Vec::with_capacity(batch_size * max_len);

        for encoding in encodings {
            let ids = encoding.get_ids();
            let mask = encoding.get_attention_mask();
            token_ids_flat.extend_from_slice(ids);
            attention_mask_flat.extend_from_slice(mask);
        }

        // 2. Transfer input tensors to Device
        let input_ids = Tensor::from_slice(&token_ids_flat, (batch_size, max_len), &self.device)
            .map_err(|e| InferenceError::TensorError(e.to_string()))?;

        let token_type_ids = input_ids
            .zeros_like()
            .map_err(|e| InferenceError::TensorError(e.to_string()))?;

        // 3. Execute GPU forward pass
        let hidden_states = self
            .model
            .forward(&input_ids, &token_type_ids, None)
            .map_err(|e| InferenceError::ForwardError(e.to_string()))?;

        // 4. Mean pooling across sequence dimension
        let (_b_size, n_tokens, _hidden_size) = hidden_states
            .dims3()
            .map_err(|e| InferenceError::TensorError(e.to_string()))?;

        let pooled = (hidden_states
            .sum(1)
            .map_err(|e| InferenceError::TensorError(e.to_string()))?
            / (n_tokens as f64))
            .map_err(|e| InferenceError::TensorError(e.to_string()))?;

        // 5. L2 Normalization (Unit vectors for cosine similarity)
        let norm = pooled
            .sqr()
            .map_err(|e| InferenceError::TensorError(e.to_string()))?
            .sum_keepdim(1)
            .map_err(|e| InferenceError::TensorError(e.to_string()))?
            .sqrt()
            .map_err(|e| InferenceError::TensorError(e.to_string()))?;

        let normalized = pooled
            .broadcast_div(&norm)
            .map_err(|e| InferenceError::TensorError(e.to_string()))?;

        // 6. Extract normalized embeddings to host memory
        let mut results = Vec::with_capacity(batch_size);
        for i in 0..batch_size {
            let row = normalized
                .get(i)
                .map_err(|e| InferenceError::TensorError(e.to_string()))?
                .to_vec1::<f32>()
                .map_err(|e| InferenceError::TensorError(e.to_string()))?;
            results.push(row);
        }

        Ok(results)
    }

    /// Convenience helper for single string embedding
    pub fn embed_text(&self, text: &str) -> Result<Vec<f32>, InferenceError> {
        let batch_result = self.embed_batch(&[text])?;
        Ok(batch_result.into_iter().next().unwrap_or_default())
    }
}
