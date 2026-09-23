# Phase 1 Data Foundation

The purpose of this phase is to establish a deterministic, auditable data layer before strategy tuning.

## Required datasets

1. Contract metadata and lot sizes from NSE.
2. NIFTY/BANKNIFTY/index spot and futures intraday bars.
3. Option bars with strike, expiry, option type, OHLC, volume and OI.
4. Option IV where available.
5. Daily context: India VIX, FII/DII and index-futures positioning where timestamp alignment permits.
6. Global context: major index/volatility proxies only when their timestamp precedes the Indian session being modeled.

## Data rules

- Store raw downloads outside Git history when the source license or size makes that necessary.
- Store source manifests, hashes, validation summaries and compact research samples in the repository.
- Cache immutable datasets by source version/hash in CI.
- Never substitute a current option chain snapshot for historical contract data.
- Never choose a strike/expiry from future information.
- Never treat close-price bars as executable mid/ask prices without a slippage penalty.

The full source list is in data/sources.yaml.
