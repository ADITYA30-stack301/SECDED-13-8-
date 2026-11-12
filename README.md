SECDED (13,8) encoder and decoder in Verilog:

A small error-correcting memory word I built while getting into automotive-style fault-tolerant design. It protects 8 data bits with a Hamming code plus one overall parity bit, so it can fix any single flipped bit and notice any double flip. Everything here is simulation only for now (Icarus Verilog), and the testbench is exhaustive, so there is no sampling or "it worked on my random seeds" involved.

What it does

The encoder takes 8 data bits and produces a 13-bit codeword: 4 Hamming check bits, 8 data bits, and 1 overall parity bit.

The decoder takes a 13-bit word that may have been damaged and gives back:

data_out: the 8 recovered data bits
corrected: a single flipped bit was found and fixed
uncorrectable: something is wrong and it can't be fixed
Codeword layout

I number codeword positions from 1 (the usual Hamming way) but store them in a Verilog vector, so bit index = position - 1.

Position	1	2	3	4	5	6	7	8	9	10	11	12	
Bit index	0	1	2	3	4	5	6	7	8	9	10	11	12
Holds	p1	p2	d1	p4	d2	d3	d4	p8	d5	d6	d7	d8	P

P, the overall parity bit, sits at index 12 and isn't part of any Hamming group.

Check bits (d1 to d8 are data[0] to data[7]):

p1 = d1 ^ d2 ^ d4 ^ d5 ^ d7
p2 = d1 ^ d3 ^ d4 ^ d6 ^ d7
p4 = d2 ^ d3 ^ d4 ^ d8
p8 = d5 ^ d6 ^ d7 ^ d8
P  = d1 ^ d2 ^ d3 ^ d5 ^ d6 ^ d8

The last one is the simplified form. P is really the XOR of all 12 other bits, but the check bits are themselves XORs of data bits, so d4 and d7 each show up an even number of times and cancel out. That leaves 6 inputs instead of 12.

How the decoder decides

It computes a 4-bit syndrome from the four groups, plus ptot, the XOR of all 13 received bits. For a single flip, the syndrome is exactly the position of the bad bit. ptot tells odd numbers of flips (1) apart from even ones (0).

Syndrome	ptot	What happened	corrected	uncorrectable
0	0	no error	0	0
0	1	only the P bit flipped	1	0
1 to 12	1	single error	1	0
13 to 15	1	impossible position	0	1
nonzero	0	double error	0	1

Two choices in there that weren't forced:

P flipped counts as corrected. The data was never wrong, but a bit did flip and the decoder dealt with it, so I raise the flag.
Syndrome 13 to 15 is uncorrectable. The code is shortened (a full Hamming code with 4 check bits would have 15 positions, this one has 12), so those syndromes can't come from a single flip. Treating them as a fix would pretend a multi-bit error is a clean single one.

The bit flip itself is a mask with one 1 at index syn - 1, XORed onto the received word. It only fires for a real single error (ptot is 1 and the syndrome is 1 to 12).

Repo layout
rtl/   secded_enc.v, secded_dec.v
tb/    secded_codec_tb.v
sim/   compiled output (ignored by git)
Running it

You need Icarus Verilog. I used 12.0 (devel) on Windows. From the project root:

iverilog -s secded_codec_tb -o sim/codec.vvp rtl/secded_enc.v rtl/secded_dec.v tb/secded_codec_tb.v
vvp sim/codec.vvp

Make sure the sim folder exists first. A passing run prints:

Encoder parity check : 0 failures / 256
No-error test        : 0 failures / 256
Single-error test    : 0 failures / 3328
Double-error test    : 0 failures / 19968
ALL TESTS PASSED
What the testbench checks
Test	Cases	What it checks
Encoder parity	256	every group, and the whole word, has even parity (uses its own copy of the group masks, so it doesn't just repeat the encoder's equations)
No error	256	data comes back unchanged, both flags stay 0
Single error	256 x 13 = 3,328	every bit flipped in turn (data, check bits and P): data restored, corrected = 1, uncorrectable = 0
Double error	256 x 78 = 19,968	every pair of bits flipped: corrected = 0, uncorrectable = 1 (data isn't checked here, since it isn't guaranteed)

That's 23,808 cases in total, and the simulation ends at 23,808 ns with 1 ns per case, which is a handy sanity check that nothing got skipped.

Does the testbench actually catch bugs?

A testbench that has only ever said PASS hasn't shown it can fail, so I broke the decoder on purpose and ran it again:

Mutation	No-error	Single	Double
none	0	0	0
syn <= 12 changed to <= 11 in corrected only	0	256	0
one bit of mask M4 flipped	128	1408	640
both of the above together	128	1536	640
(syn > 0) removed from the flip enable	0	0	0

The <= 11 case fails on exactly the 256 inputs that go through syndrome 12. The M4 change breaks the syndrome for about half of all inputs, which shows up in every test except the encoder check (which never touches the decoder).

The last row is an equivalent mutant: in simulation, shifting by syn - 1 when syn is 0 pushes the 1 out of the 13-bit word, so nothing flips anyway. I kept the guard in the real design because I'd rather not depend on shift overflow behaving the same way in synthesis.

What this does not cover yet
Only up to two flipped bits are tested. SECDED guarantees nothing beyond that, and I haven't measured what happens with three or more.
No comparison against an unprotected word or a parity-only word yet.
No area or timing numbers, and no FPGA run. All results so far are from simulation.
It's an 8-bit word. Wider words need more check bits (the number grows roughly with the log of the width).

Planned next: triple-flip statistics, the baseline comparisons, synthesis numbers, then an FPGA port.