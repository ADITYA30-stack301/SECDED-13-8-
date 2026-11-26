"""Regenerate model/ber_sweep.png and model/ber_theory_overlay.png from model/sweep.csv.

Run from anywhere:  python model/make_plots.py
Needs: numpy, matplotlib. sweep.csv comes from  python model/pipeline_model.py
"""
import csv
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(os.path.dirname(HERE), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
rows = list(csv.DictReader(open(os.path.join(HERE, "sweep.csv"))))
col = lambda k: np.array([float(r[k]) for r in rows])

p = col("p")
secded_ber, raw_ber = col("secded_crc_post_ber"), col("raw_post_ber")
retx, raw_retx = col("frames_retransmit"), col("raw_frames_retransmit")
undetected = col("frames_undetected")

# ---------- Plot 1: BER and frame outcomes ----------
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].loglog(p, p, "k--", label="p (no coding)")
ax[0].loglog(p, raw_ber, "o", label="CRC only")
ax[0].loglog(p, secded_ber, "s-", label="SECDED(13,8) + CRC-8")
ax[0].set_xlabel("channel bit-flip probability p")
ax[0].set_ylabel("payload BER after decode")
ax[0].legend()
ax[0].grid(True, which="both", alpha=0.3)

ax[1].loglog(p, retx, "s-", label="SECDED+CRC: retransmit rate")
ax[1].loglog(p, raw_retx, "o-", label="CRC only: retransmit rate")
mask = undetected > 0
if mask.any():
    ax[1].loglog(p[mask], undetected[mask], "^", label="SECDED+CRC: undetected frames")
ax[1].set_xlabel("p")
ax[1].set_ylabel("fraction of frames")
ax[1].legend(fontsize=8)
ax[1].grid(True, which="both", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(RESULTS_DIR, "ber_sweep.png"), dpi=140)
plt.close(fig)

# ---------- Plot 2: theory overlay ----------
pp = np.logspace(np.log10(p.min()), np.log10(p.max()), 200)
P01 = (1 - pp) ** 13 + 13 * pp * (1 - pp) ** 12      # 0 or 1 flip in a 13-bit codeword
theory = 1 - P01 ** 9                                # any of the 9 codewords has >= 2 flips
raw_theory = 1 - (1 - pp) ** 72                      # any of 72 uncoded bits flipped

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].loglog(pp, theory, "-", label="theory: 1-(P0+P1)^9")
ax[0].loglog(p, retx, "s", label="simulation (SECDED+CRC)")
ax[0].loglog(pp, raw_theory, "--", label="theory: no ECC, 72 bits")
ax[0].loglog(p, raw_retx, "o", mfc="none", label="simulation (CRC only)")
ax[0].set_xlabel("p")
ax[0].set_ylabel("frame retransmit rate")
ax[0].legend(fontsize=8)
ax[0].grid(True, which="both", alpha=0.3)

ax[1].loglog(p, secded_ber, "s-", label="simulated payload BER (SECDED)")
ax[1].loglog(pp, pp, "k--", label="uncoded")
ax[1].loglog(pp, 40 * pp ** 2, ":", label="~p^2 reference (slope 2)")
ax[1].set_xlabel("p")
ax[1].set_ylabel("payload BER")
ax[1].legend(fontsize=8)
ax[1].grid(True, which="both", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(RESULTS_DIR, "ber_theory_overlay.png"), dpi=140)
plt.close(fig)

# Agreement between simulation and the closed form
sim_theory = 1 - ((1 - p) ** 13 + 13 * p * (1 - p) ** 12) ** 9
rel = np.abs(retx - sim_theory) / sim_theory
print(f"wrote ber_sweep.png and ber_theory_overlay.png in {RESULTS_DIR}")
print(f"max relative deviation, retransmit rate vs closed form: {rel.max():.1%} (at p={p[rel.argmax()]:.2e})")
