# SECDED (13,8) Encoder and Decoder in Verilog

A simulation-based implementation of a **Single Error Correction, Double Error Detection (SECDED)** memory word using Verilog HDL.

This project was built while exploring fault-tolerant digital design and automotive-style safety mechanisms. It protects 8 data bits using a shortened Hamming code with an additional overall parity bit.

The design can:
- Correct any single-bit error.
- Detect any double-bit error.
- Identify uncorrectable error conditions.
- Verify functionality through exhaustive simulation rather than random testing.

**Tools:** Verilog HDL · Icarus Verilog 12.0 · GTKWave (optional)

**Implementation status:** Simulation only. No FPGA hardware validation yet.

---

## 1. Architecture

The design consists of two main modules:

| Module | Function |
|---|---|
| `secded_enc` | Encodes 8 data bits into a 13-bit SECDED codeword |
| `secded_dec` | Detects and corrects single-bit errors and flags double-bit errors |

### Encoder

The encoder accepts an 8-bit input and generates a 13-bit codeword containing:

- 8 data bits
- 4 Hamming check bits
- 1 overall parity bit

### Decoder

The decoder accepts a potentially corrupted 13-bit codeword and produces:

| Output | Description |
|---|---|
| `data_out` | Recovered 8-bit data |
| `corrected` | Indicates that a single-bit error was corrected |
| `uncorrectable` | Indicates an uncorrectable error condition |

---

## 2. Codeword Layout

The first 12 positions follow the conventional Hamming code arrangement. The overall parity bit occupies the 13th position.

**Verilog bit index = codeword position − 1**

| Position | Bit index | Contents |
|:---:|:---:|:---:|
| 1 | 0 | p1 |
| 2 | 1 | p2 |
| 3 | 2 | d1 |
| 4 | 3 | p4 |
| 5 | 4 | d2 |
| 6 | 5 | d3 |
| 7 | 6 | d4 |
| 8 | 7 | p8 |
| 9 | 8 | d5 |
| 10 | 9 | d6 |
| 11 | 10 | d7 |
| 12 | 11 | d8 |
| 13 | 12 | P (overall parity) |

The data mapping is:

`d1` through `d8` correspond to `data[0]` through `data[7]`.

### Parity Equations

The four Hamming parity bits are calculated as:

```verilog
p1 = d1 ^ d2 ^ d4 ^ d5 ^ d7;
p2 = d1 ^ d3 ^ d4 ^ d6 ^ d7;
p4 = d2 ^ d3 ^ d4 ^ d8;
p8 = d5 ^ d6 ^ d7 ^ d8;
```

The overall parity bit is:

```verilog
P = d1 ^ d2 ^ d3 ^ d5 ^ d6 ^ d8;
```

This is a simplified expression.

The overall parity bit is conceptually the XOR of all 12 other codeword bits. Since the Hamming check bits are themselves XOR combinations of data bits, substituting their expressions causes `d4` and `d7` to cancel out.

Consequently, the simplified equation requires only six data-bit inputs.

---

## 3. Decoder Logic

The decoder calculates two important quantities:

1. **Syndrome:** A 4-bit value obtained from the four Hamming parity groups.
2. **Overall parity (`ptot`):** XOR of all 13 received bits.

The syndrome identifies the position of a single-bit error, while overall parity distinguishes odd-numbered errors from even-numbered errors.

### Error Classification

| Syndrome | `ptot` | Interpretation | Corrected | Uncorrectable |
|:---:|:---:|---|:---:|:---:|
| 0 | 0 | No error | 0 | 0 |
| 0 | 1 | Overall parity bit flipped | 1 | 0 |
| 1–12 | 1 | Single-bit error | 1 | 0 |
| 13–15 | 1 | Invalid shortened-code position | 0 | 1 |
| Nonzero | 0 | Double-bit error | 0 | 1 |

### Correction Mechanism

For a valid single-bit error, the decoder generates a correction mask:

```verilog
corrected_word = received_word ^ (13'b1 << (syn - 1));
```

The correction is enabled only when:

- `ptot = 1`
- Syndrome is between 1 and 12.

The overall parity bit is handled separately because it is located at bit index 12 and is not part of the four Hamming parity groups.

### Design Decisions

Two implementation choices deserve attention:

**1. Overall parity-bit correction**

When only the overall parity bit flips, the syndrome remains zero and `ptot` becomes one.

The data is already correct, but the decoder asserts `corrected` because a single-bit error has been identified and handled.

**2. Invalid syndrome handling**

Syndromes 13, 14 and 15 do not correspond to valid positions in this shortened Hamming code.

The decoder flags these conditions as uncorrectable rather than attempting an invalid correction.

---

## 4. Repository Structure

```text
SECDED-13-8/
│
├── rtl/
│   ├── secded_enc.v
│   └── secded_dec.v
│
├── tb/
│   └── secded_codec_tb.v
│
├── sim/
│   └── (compiled simulation output)
│
├── .gitignore
└── README.md
```

---

## 5. Simulation and Verification

The design was verified using **Icarus Verilog 12.0 (development build)**.

### Prerequisites

- Icarus Verilog
- VS Code (recommended)
- GTKWave (optional, for waveform inspection)

### Running the Simulation

Execute the following commands from the project root.

First, ensure the simulation directory exists:

```powershell
New-Item -ItemType Directory -Force sim
```

Compile the design:

```bash
iverilog -s secded_codec_tb -o sim/codec.vvp rtl/secded_enc.v rtl/secded_dec.v tb/secded_codec_tb.v
```

Run the simulation:

```bash
vvp sim/codec.vvp
```

### Expected Output

```text
Encoder parity check : 0 failures / 256
No-error test        : 0 failures / 256
Single-error test    : 0 failures / 3328
Double-error test    : 0 failures / 19968

ALL TESTS PASSED
```

---

## 6. Exhaustive Testbench Coverage

The testbench evaluates all 256 possible 8-bit input combinations.

| Test | Number of Cases | Verification |
|---|---:|---|
| Encoder parity | 256 | Checks even parity across all four Hamming groups and overall parity |
| No-error test | 256 | Verifies unchanged data and inactive error flags |
| Single-error test | 3,328 | Tests all 13 possible single-bit flips for every input |
| Double-error test | 19,968 | Tests all 78 possible pairs of flipped bits for every input |
| **Total** | **23,808** | **Exhaustive verification** |

### Independent Parity Verification

The encoder parity check uses independently defined parity masks in the testbench.

For each Hamming group:

```verilog
^(code & M1) == 0
```

The same check is performed for the other three groups.

Overall parity is independently verified using:

```verilog
^code == 0
```

This avoids simply repeating the encoder's parity equations in the testbench and provides an independent consistency check.

### Single-Bit Error Testing

For each of the 256 possible input combinations:

- Each of the 13 codeword bits is flipped individually.
- The decoder must recover the original data.
- `corrected` must be asserted.
- `uncorrectable` must remain deasserted.

Total cases:

**256 × 13 = 3,328**

### Double-Bit Error Testing

For each input combination:

- All possible pairs of codeword bits are flipped.
- The decoder must assert `uncorrectable`.
- `corrected` must remain deasserted.

There are:

\[
\binom{13}{2} = 78
\]

Total cases:

**256 × 78 = 19,968**

The recovered data is not checked in this test because SECDED does not guarantee correct recovery from double-bit errors.

### Simulation Duration

The testbench uses a 1 ns interval per test case.

The expected total simulation time is:

**23,808 ns**

This provides an additional sanity check that all planned test cases were executed.

---

## 7. Mutation Testing

A passing testbench does not necessarily prove that the testbench itself can detect implementation bugs.

To evaluate its effectiveness, intentional mutations were introduced into the decoder and the simulation was repeated.

| Mutation | No-error failures | Single-error failures | Double-error failures |
|---|---:|---:|---:|
| Original design | 0 | 0 | 0 |
| Change `syn <= 12` to `syn <= 11` in correction flag logic | 0 | 256 | 0 |
| Flip one bit of mask M4 | 128 | 1,408 | 640 |
| Apply both mutations | 128 | 1,536 | 640 |
| Remove `(syn > 0)` from correction enable | 0 | 0 | 0 |

### Mutation Analysis

**Mutation 1: Incorrect syndrome boundary**

Changing the correction condition from `syn <= 12` to `syn <= 11` causes the decoder to fail for all 256 input combinations when the error occurs at syndrome position 12.

This confirms that the testbench covers the highest valid syndrome position.

**Mutation 2: Incorrect parity mask**

Flipping one bit in M4 affects syndrome generation for a subset of inputs.

The resulting failures appear across no-error, single-error and double-error tests.

**Mutation 3: Removing the zero-syndrome guard**

Removing `(syn > 0)` from the correction enable produced no failures in simulation.

This is an equivalent mutant for the tested implementation: when the syndrome is zero, the attempted shift does not produce a correction bit in the 13-bit word.

The guard is retained in the original design to make the intended correction condition explicit and avoid depending on shift-width behavior.

### Why Mutation Testing Matters

Mutation testing helps evaluate whether the testbench can detect specific classes of implementation defects.

It provides additional confidence beyond simply observing a successful simulation.

---

## 8. Limitations

The current implementation has several limitations:

- Verification covers only zero, single-bit and double-bit error conditions.
- SECDED does not guarantee correct recovery from three or more bit errors.
- No comparison has been performed against an unprotected data word or parity-only implementation.
- No synthesis-based area or timing measurements are available.
- No FPGA hardware validation has been performed.
- The current implementation supports an 8-bit data word.

Wider data words require additional Hamming parity bits, with the number of check bits determined by the Hamming-code sizing condition.

---

## 9. Future Work

The following extensions are planned:

- [ ] Triple-bit error analysis and statistical evaluation.
- [ ] Comparison with parity-only and unprotected memory implementations.
- [ ] Logic synthesis and area estimation.
- [ ] Timing analysis.
- [ ] FPGA implementation and hardware validation.
- [ ] Extension to wider data words.
- [ ] Investigation of SECDED applications in automotive embedded systems and safety-oriented memory architectures.

---

## 10. Project Motivation

This project explores how error detection and correction can improve the reliability of digital systems.

SECDED is particularly relevant to memory protection, fault-tolerant computing and safety-oriented embedded architectures.

The project focuses not only on implementing an encoder and decoder, but also on understanding parity mathematics, syndrome-based error localization, exhaustive verification and mutation testing.

**Current focus:** Moving from simulation-based verification toward synthesis, implementation and quantitative hardware analysis.