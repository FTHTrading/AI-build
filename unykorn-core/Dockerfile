FROM rust:1.80-slim AS builder
WORKDIR /usr/src/unykorn

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config libssl-dev libclang-dev clang build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY . .
RUN cargo build --release --bin unykorn-node

FROM debian:bookworm-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libssl3 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/src/unykorn/target/release/unykorn-node /app/unykorn-node

EXPOSE 8791
CMD ["/app/unykorn-node"]
