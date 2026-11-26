"""
Golden model: CRC-8 + SECDED(13,8) pipeline over a binary symmetric channel (BSC).

Frame   : 8 payload bytes + 1 CRC-8 byte = 9 bytes
Code    : each byte -> 13-bit extended Hamming (SECDED) codeword
Channel : each of the 117 bits flips independently with probability p
Outcomes per frame:
  clean       - no bit flipped
  corrected   - flips occurred, every codeword decoded OK, CRC passes, payload correct
  detected    - decoder flags a double error OR CRC fails  -> receiver would request retransmit
  undetected  - CRC passes but payload is wrong            -> silent data corruption (the bad one)
"""
import numpy as np
import os
# ---------- SECDED(13,8) ----------
# Hamming positions 1..12: parity at 1,2,4,8; data at 3,5,6,7,9,10,11,12. Bit 0 of word = overall parity.
DATA_POS = [3, 5, 6, 7, 9, 10, 11, 12]
PAR_POS = [1, 2, 4, 8]


def secded_encode(d):
    bits = [0] * 13  # index 1..12 Hamming, index 0 overall parity
    for i, pos in enumerate(DATA_POS):
        bits[pos] = (d >> i) & 1
    for p in PAR_POS:
        s = 0
        for pos in range(1, 13):
            if pos & p and pos != p:
                s ^= bits[pos]
        bits[p] = s
    bits[0] = 0
    bits[0] = sum(bits) & 1
    return sum(b << i for i, b in enumerate(bits))


OK, CORRECTED, DOUBLE = 0, 1, 2


def secded_decode(w):
    bits = [(w >> i) & 1 for i in range(13)]
    syn = 0
    for pos in range(1, 13):
        if bits[pos]:
            syn ^= pos
    overall = sum(bits) & 1  # 0 means overall parity consistent
    if syn == 0 and overall == 0:
        status = OK
    elif overall == 1:       # odd number of errors -> assume single, correct it
        status = CORRECTED
        if 1 <= syn <= 12:
            bits[syn] ^= 1
        elif syn == 0:       # error was in the overall parity bit
            bits[0] ^= 1
        else:                # syndrome points outside the code -> can't be a single error
            status = DOUBLE
    else:                    # syn != 0, overall parity ok -> even number (>=2) of errors
        status = DOUBLE
    d = sum(bits[pos] << i for i, pos in enumerate(DATA_POS))
    return d, status


ENC = np.array([secded_encode(d) for d in range(256)], dtype=np.int32)
DEC_D = np.zeros(1 << 13, dtype=np.int32)
DEC_S = np.zeros(1 << 13, dtype=np.int32)
for w in range(1 << 13):
    DEC_D[w], DEC_S[w] = secded_decode(w)

# sanity: every single-bit error is corrected; every double-bit error is flagged
for d in range(256):
    cw = secded_encode(d)
    for i in range(13):
        dd, s = secded_decode(cw ^ (1 << i))
        assert dd == d and s == CORRECTED
        for j in range(i + 1, 13):
            _, s2 = secded_decode(cw ^ (1 << i) ^ (1 << j))
            assert s2 == DOUBLE


# ---------- CRC-8 (poly 0x07) ----------
def crc8_table():
    t = []
    for b in range(256):
        c = b
        for _ in range(8):
            c = ((c << 1) ^ 0x07) & 0xFF if c & 0x80 else (c << 1) & 0xFF
        t.append(c)
    return np.array(t, dtype=np.int32)


CRC_T = crc8_table()


def crc8_batch(payload):  # payload shape (F, n) -> (F,)
    c = np.zeros(payload.shape[0], dtype=np.int32)
    for k in range(payload.shape[1]):
        c = CRC_T[c ^ payload[:, k]]
    return c


# ---------- simulation ----------
NB = 8
W = 13
WEIGHTS = (1 << np.arange(W)).astype(np.int32)


def simulate(p, frames, rng):
    payload = rng.integers(0, 256, size=(frames, NB), dtype=np.int32)
    frame = np.concatenate([payload, crc8_batch(payload)[:, None]], axis=1)  # (F, 9)
    cw = ENC[frame]                                                          # (F, 9)
    flips = rng.random((frames, NB + 1, W)) < p
    err = (flips * WEIGHTS).sum(axis=2).astype(np.int32)
    rx = cw ^ err
    n_flips = flips.sum(axis=(1, 2))
    dec = DEC_D[rx]
    flagged = (DEC_S[rx] == DOUBLE).any(axis=1)
    rx_payload, rx_crc = dec[:, :NB], dec[:, NB]
    crc_ok = crc8_batch(rx_payload) == rx_crc
    payload_ok = (rx_payload == payload).all(axis=1)
    no_err = n_flips == 0
    detected = flagged | ~crc_ok
    undetected = ~detected & ~payload_ok
    delivered_ok = ~detected & payload_ok
    corrected = delivered_ok & ~no_err
    # post-decode payload bit errors (what the app would see if it ignored flags)
    bit_err = np.unpackbits((rx_payload ^ payload).astype(np.uint8)[..., None], axis=2).sum()
    return dict(
        p=p,
        clean=no_err.mean(),
        corrected=corrected.mean(),
        detected=detected.mean(),
        undetected=undetected.mean(),
        post_ber=bit_err / (frames * NB * 8),
    )


def simulate_raw(p, frames, rng):
    """Baseline with no ECC: 72 uncoded bits, CRC only (detects, cannot correct)."""
    payload = rng.integers(0, 256, size=(frames, NB), dtype=np.int32)
    frame = np.concatenate([payload, crc8_batch(payload)[:, None]], axis=1)
    bits = np.unpackbits(frame.astype(np.uint8)[..., None], axis=2)  # (F,9,8)
    flips = rng.random(bits.shape) < p
    rx = np.packbits(bits ^ flips, axis=2).squeeze(2).astype(np.int32)
    crc_ok = crc8_batch(rx[:, :NB]) == rx[:, NB]
    payload_ok = (rx[:, :NB] == payload).all(axis=1)
    detected = ~crc_ok
    return dict(p=p, detected=detected.mean(), undetected=(~detected & ~payload_ok).mean(),
                post_ber=np.unpackbits((rx[:, :NB] ^ payload).astype(np.uint8)[..., None], axis=2).sum() / (frames * NB * 8))


if __name__ == "__main__":
    import csv
    rng = np.random.default_rng(2026)
    ps = np.logspace(-3.5, -0.8, 14)
    rows = []
    for p in ps:
        F = 400_000
        a = simulate(p, F, rng)
        b = simulate_raw(p, F, rng)
        rows.append(dict(p=p, secded_crc_post_ber=a["post_ber"], raw_post_ber=b["post_ber"],
                         frames_retransmit=a["detected"], frames_undetected=a["undetected"],
                         raw_frames_retransmit=b["detected"], raw_frames_undetected=b["undetected"]))
        print(f"p={p:.2e}  postBER secded={a['post_ber']:.2e} raw={b['post_ber']:.2e}  "
              f"retx={a['detected']:.3e}  undetected={a['undetected']:.2e}")
    HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "sweep.csv")

with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
