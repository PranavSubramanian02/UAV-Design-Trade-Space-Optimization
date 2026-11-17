# Academic Literature & Theoretical Benchmarks for Project 2: UAV Design Trade Space Optimization

This document synthesizes the academic foundations, peer-reviewed equations, and benchmark methodologies used to rebuild Project 2 from the ground up into a publication-grade Multidisciplinary Design Optimization (MDO) framework.

---

## 1. Verified Peer-Reviewed Literature Matrix

| Paper / Reference | Venue / Identifier | Key Mathematical Contribution to Project 2 | Status |
| :--- | :--- | :--- | :--- |
| **Traub, Lance W. (2011)**<br>*"Range and Endurance Estimates for Battery-Powered Aircraft"* | **AIAA Journal of Aircraft**<br>Vol. 48, No. 2, pp. 703–707<br>DOI: [`10.2514/1.C031027`](https://doi.org/10.2514/1.C031027) | **Peukert C-rate discharge derating**:<br>$C_{\text{eff}} = C \cdot (I_{\text{ref}}/I)^{k_p - 1}$. Replaces static energy equations with dynamic rate-dependent capacity for electric aircraft. | Verified CrossRef<br>(High Confidence, 195 citations) |
| **Donateo, Teresa et al. (2017)**<br>*"A new approach to calculating endurance in electric flight and comparing fuel cells and batteries"* | **Applied Energy**<br>Vol. 187, pp. 807–819<br>DOI: [`10.1016/j.apenergy.2016.11.100`](https://doi.org/10.1016/j.apenergy.2016.11.100) | **Mission-based energy segmentation**:<br>Decomposes electric flight into climb, cruise, loiter, and reserve segments with battery state-of-charge tracking. | Verified CrossRef<br>(High Confidence) |
| **Deb, Kalyanmoy et al. (2002)**<br>*"A fast and elitist multiobjective genetic algorithm: NSGA-II"* | **IEEE Trans. Evolutionary Computation**<br>Vol. 6, No. 2, pp. 182–197<br>DOI: [`10.1109/4235.996017`](https://doi.org/10.1109/4235.996017) | **Non-Dominated Sorting & Crowding Distance**:<br>Replaces the legacy $O(N^2)$ scalar filter with authentic multi-objective Pareto front extraction. | Verified CrossRef<br>(High Confidence, 60,000+ citations) |
| **Burela, A. G. & Sujit, P. B. (2026)**<br>*"Multi-Domain Physics-Based MDO of Multirotor UAVs: A Deterministic Framework for Discrete COTS Sizing"* | **arXiv:2607.22768**<br>[cs.CE, cs.RO, eess.SY]<br>[PDF on Disk](file:///home/pranav/Documents/AEROSPACE/Resume%20Projects/Research%20Papers/Project%202/Burela_Sujit_2026_MDO_Mass_Snowball_Effect.pdf) | **Mass Snowball Effect & Picard Iteration**:<br>Proves that sequential sizing triggers a mass-compounding divergence. Solves the coupled fixed-point loop ($W_{0,k+1} = \mathcal{F}(W_{0,k})$) within 25–50 iterations. | Full PDF Saved in `Research Papers/Project 2/` |
| **Tfaily, A., Diouane, Y., Bartoli, N., Kokkolaras, M. (2026)**<br>*"Transfer Learning in Bayesian Optimization for Aircraft Design"* | **arXiv:2603.28999**<br>[math.OC, cs.LG]<br>[PDF on Disk](file:///home/pranav/Documents/AEROSPACE/Resume%20Projects/Research%20Papers/Project%202/Tfaily_2026_Bayesian_Optimization_Aircraft_Design.pdf) | **Surrogate Modeling in Aircraft MDO**:<br>Gaussian Process and Kriging surrogate modeling for constrained aircraft trade-space exploration. | Full PDF Saved in `Research Papers/Project 2/` |
| **Raymer, Daniel P.**<br>*"Aircraft Design: A Conceptual Approach"* | **AIAA Education Series** | **Converged Weight Sizing & Spar Bending**:<br>Wing root bending moment formulation ($M_{\text{root}} = \frac{n_{\text{ult}} W_0 b}{2\pi}$) and Oswald factor $e(AR)$ scaling. | Textbook Benchmark |

---

## 2. Core Mathematical Formulations from the Literature

### 1. The Traub Electric Aircraft Endurance Law (Traub 2011)
Traub demonstrated that the classical Breguet endurance formula fails for electric aircraft because batteries do not lose mass as they discharge, and high discharge rates prematurely terminate usable battery capacity (the Peukert effect):

$$E_{\text{actual}} = \left( \frac{e_{\text{nominal}} \cdot m_{\text{batt}}}{P_{\text{req}}} \right)^{1/k_p} \cdot \left( \frac{\eta_{\text{total}}}{V_{\text{bus}}} \right)^{\frac{k_p - 1}{k_p}}$$

Where $k_p \approx 1.05 - 1.15$ is Peukert's exponent. For a typical LiPo/Li-ion battery at high climb power (2C–3C rate), this reduces delivered energy by **$12\% - 18\%$**, which must be accounted for in the sizing loop.

### 2. The Mass Snowball Picard Sizing Loop (Burela & Sujit 2026 / Raymer)
The gross takeoff mass $W_0$ is governed by the implicit nonlinear contraction:

$$W_{0, k+1} = W_{\text{payload}} + W_{\text{avionics}} + W_{\text{struct}}(W_{0,k}, AR, b) + W_{\text{batt}}(W_{0,k})$$

Using under-relaxation with factor $\omega = 0.5$:
$$W_{0, k+1} = (1 - \omega) W_{0, k} + \omega \left[ W_{\text{payload}} + W_{\text{avionics}} + W_{\text{struct}} + W_{\text{batt}} \right]$$
The iteration converges monotonically when $|W_{0, k+1} - W_{0, k}| < 10^{-4}\,\text{kg}$.

### 3. Aeroelastic Wing Spar Bending Moment (Raymer / Megson)
Root bending moment under $n_{\text{ult}} = 3.8\,\text{g}$ pull-up:
$$M_{\text{root}} = \frac{n_{\text{ult}} W_0 b}{3 \pi}$$
Spar cap cross-sectional area:
$$A_{\text{cap}} = \frac{M_{\text{root}}}{\sigma_{\text{allow}} (t/c) c_{\text{root}}}$$
Wing structural mass:
$$m_{\text{wing}} = 2 \rho_{\text{CFRP}} A_{\text{cap}} \frac{b}{2} + \rho_{\text{skin}} 2 S_{\text{wing}} = k_{\text{spar}} \frac{n_{\text{ult}} W_0 b^2}{\sigma_{\text{allow}} (t/c)} + k_{\text{skin}} S$$
Notice that $m_{\text{wing}} \propto b^2 = AR \cdot S$, introducing the exact physical quadratic mass penalty that balances induced drag reduction.
